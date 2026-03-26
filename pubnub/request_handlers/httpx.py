import logging
import socket
import time
import threading
import httpx
import json  # noqa # pylint: disable=W0611
import urllib


from pubnub import utils
from pubnub.enums import PNStatusCategory
from pubnub.errors import PNERR_CLIENT_ERROR, PNERR_UNKNOWN_ERROR, PNERR_TOO_MANY_REDIRECTS_ERROR, \
    PNERR_CLIENT_TIMEOUT, PNERR_HTTP_ERROR, PNERR_CONNECTION_ERROR
from pubnub.errors import PNERR_SERVER_ERROR
from pubnub.exceptions import PubNubException
from pubnub.request_handlers.base import BaseRequestHandler
from pubnub.structures import RequestOptions, PlatformOptions, ResponseInfo, Envelope

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


logger = logging.getLogger("pubnub")


class WallClockDeadlineWatchdog:
    """Persistent single-thread watchdog that enforces wall-clock deadlines on HTTP requests.

    On macOS and Linux, socket timeouts use monotonic time (mach_absolute_time / CLOCK_MONOTONIC)
    which doesn't advance during system sleep. A 310-second subscribe timeout can take hours of
    wall-clock time if the machine sleeps. This watchdog periodically checks time.time() (wall clock)
    and closes the HTTP session when the deadline passes, causing the blocking socket read to fail.

    A single daemon thread is reused across requests to avoid thread creation overhead on
    high-frequency subscribe loops (where messages arrive rapidly and each long-poll returns quickly).
    Deadlines are tracked per calling thread, so concurrent requests (e.g., subscribe + publish
    on different threads) don't interfere with each other.
    """

    CHECK_INTERVAL = 5.0

    def __init__(self):
        self._lock = threading.Lock()
        self._deadlines = {}
        self._triggered_threads = set()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread = None

    def _ensure_started(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True,
                                            name="pubnub-wall-clock-watchdog")
            self._thread.start()

    def set_deadline(self, session, deadline):
        """Arm the watchdog for the calling thread's request."""
        thread_id = threading.get_ident()
        with self._lock:
            self._deadlines[thread_id] = (session, deadline)
            self._triggered_threads.discard(thread_id)
            self._ensure_started()
        self._wake.set()

    def clear_deadline(self):
        """Disarm the watchdog for the calling thread's request."""
        thread_id = threading.get_ident()
        with self._lock:
            self._deadlines.pop(thread_id, None)
            self._triggered_threads.discard(thread_id)

    @property
    def triggered(self):
        """Check if the watchdog triggered for the calling thread."""
        return threading.get_ident() in self._triggered_threads

    def stop(self):
        """Stop the watchdog thread permanently (call on handler cleanup)."""
        self._stop.set()
        self._wake.set()

    @staticmethod
    def _force_shutdown_connections(session):
        """Force-interrupt blocked socket reads by shutting down raw TCP sockets.

        On macOS (BSD), socket.close() from another thread does NOT interrupt a blocked
        recv(). Only socket.shutdown(SHUT_RDWR) reliably unblocks it across platforms.

        We access httpcore internals to reach the raw socket:
          session._transport._pool._connections[i]._connection._network_stream._sock
        This is wrapped in try/except so version changes in httpcore degrade gracefully
        to session.close() behavior.

        Tested with: httpx 0.28.1, httpcore 1.0.9
        """
        try:
            transport = getattr(session, '_transport', None)
            pool = getattr(transport, '_pool', None) if transport else None
            connections = getattr(pool, '_connections', []) if pool else []
            for conn in list(connections):
                try:
                    inner = getattr(conn, '_connection', None)
                    if inner is None:
                        continue
                    stream = getattr(inner, '_network_stream', None)
                    if stream is None:
                        continue
                    sock = getattr(stream, '_sock', None)
                    if sock is None:
                        continue
                    sock.shutdown(socket.SHUT_RDWR)
                except (OSError, Exception):
                    pass
        except Exception as e:
            logger.debug(f"Error iterating connection pool: {e}")
        try:
            session.close()
        except Exception as e:
            logger.debug(f"Error closing session: {e}")

    def _run(self):
        while not self._stop.is_set():
            with self._lock:
                has_deadlines = bool(self._deadlines)
                if has_deadlines:
                    # Find the earliest deadline across all tracked threads
                    earliest_tid = None
                    earliest_deadline = float('inf')
                    earliest_session = None
                    for tid, (session, deadline) in self._deadlines.items():
                        if deadline < earliest_deadline:
                            earliest_deadline = deadline
                            earliest_tid = tid
                            earliest_session = session

            if not has_deadlines:
                # No active deadlines — idle until set_deadline() or stop()
                self._wake.wait()
                self._wake.clear()
                continue

            remaining = earliest_deadline - time.time()
            if remaining <= 0:
                with self._lock:
                    current = self._deadlines.get(earliest_tid)
                    if current is None or current[1] != earliest_deadline:
                        continue
                    self._triggered_threads.add(earliest_tid)
                    self._deadlines.pop(earliest_tid, None)
                logger.debug("Wall-clock deadline exceeded, closing session transport")
                self._force_shutdown_connections(earliest_session)
                continue

            # Sleep until next check, new deadline, or stop
            self._wake.wait(timeout=min(self.CHECK_INTERVAL, remaining))
            self._wake.clear()


class HttpxRequestHandler(BaseRequestHandler):
    """ PubNub Python SDK synchronous requests handler based on `httpx` HTTP library. """
    ENDPOINT_THREAD_COUNTER: int = 0

    def __init__(self, pubnub):
        self._session = None
        self._session_lock = threading.Lock()
        self._watchdog = WallClockDeadlineWatchdog()

        self.pubnub = pubnub

    def _ensure_session(self):
        """Return the current httpx.Client, creating one if needed. Thread-safe."""
        with self._session_lock:
            if self._session is None or self._session.is_closed:
                logger.debug("Creating new HTTP session")
                self._session = httpx.Client()
            return self._session

    def close(self):
        """Clean up resources: stop the watchdog thread and close the HTTP session."""
        self._watchdog.stop()
        with self._session_lock:
            if self._session is not None:
                self._session.close()

    async def async_request(self, options_func, cancellation_event):
        raise NotImplementedError("async_request is not implemented for synchronous handler")

    def sync_request(self, platform_options, endpoint_call_options):
        return self._build_envelope(platform_options, endpoint_call_options)

    def threaded_request(self, endpoint_name, platform_options, endpoint_call_options, callback, cancellation_event):
        call = Call()

        if cancellation_event is None:
            cancellation_event = threading.Event()

        def callback_to_invoke_in_separate_thread():
            try:
                envelope = self._build_envelope(platform_options, endpoint_call_options)
                if cancellation_event is not None and cancellation_event.is_set():
                    # Since there are no way to affect on ongoing request it's response will
                    # be just ignored on cancel call
                    return
                callback(envelope)
            except PubNubException as e:
                logger.error("Async request PubNubException. %s" % str(e))
                callback(Envelope(
                    result=None,
                    status=endpoint_call_options.create_status(
                        category=PNStatusCategory.PNBadRequestCategory,
                        response=None,
                        response_info=None,
                        exception=e)))
            except Exception as e:
                logger.error("Async request Exception. %s" % str(e))

                callback(Envelope(
                    result=None,
                    status=endpoint_call_options.create_status(
                        category=PNStatusCategory.PNInternalExceptionCategory,
                        response=None,
                        response_info=None,
                        exception=e)))
            finally:
                call.executed_cb()

        self.execute_callback_in_separate_thread(
            callback_to_invoke_in_separate_thread,
            endpoint_name,
            call,
            cancellation_event
        )

    def execute_callback_in_separate_thread(
            self, callback_to_invoke_in_another_thread, operation_name, call_obj, cancellation_event
    ):
        client = AsyncHTTPClient(callback_to_invoke_in_another_thread)

        HttpxRequestHandler.ENDPOINT_THREAD_COUNTER += 1

        thread = threading.Thread(
            target=client.run,
            name=f"Thread-{operation_name}-{HttpxRequestHandler.ENDPOINT_THREAD_COUNTER}",
            daemon=self.pubnub.config.daemon
        ).start()

        call_obj.thread = thread
        call_obj.cancellation_event = cancellation_event

        return call_obj

    def async_file_based_operation(self, func, callback, operation_name, cancellation_event=None):
        call = Call()

        if cancellation_event is None:
            cancellation_event = threading.Event()

        def callback_to_invoke_in_separate_thread():
            try:
                envelope = func()
                callback(envelope.result, envelope.status)
            except Exception as e:
                logger.error("Async file upload request Exception. %s" % str(e))
                callback(
                    Envelope(result=None, status=e)
                )
            finally:
                call.executed_cb()

        self.execute_callback_in_separate_thread(
            callback_to_invoke_in_separate_thread,
            operation_name,
            call,
            cancellation_event
        )

        return call

    def _build_envelope(self, p_options, e_options):
        """ A wrapper for _invoke_url to separate request logic """

        status_category = PNStatusCategory.PNUnknownCategory
        response_info = None

        url_base_path = self.pubnub.base_origin if e_options.use_base_path else None
        try:
            res = self._invoke_request(p_options, e_options, url_base_path)
        except PubNubException as e:
            if e._pn_error in [PNERR_CONNECTION_ERROR, PNERR_UNKNOWN_ERROR]:
                status_category = PNStatusCategory.PNUnexpectedDisconnectCategory
            elif e._pn_error is PNERR_CLIENT_TIMEOUT:
                status_category = PNStatusCategory.PNTimeoutCategory

            return Envelope(
                result=None,
                status=e_options.create_status(
                    category=status_category,
                    response=None,
                    response_info=response_info,
                    exception=e))

        if res is not None:
            query = urllib.parse.parse_qs(res.url.query)
            uuid = None
            auth_key = None

            if 'uuid' in query and len(query['uuid']) > 0:
                uuid = query['uuid'][0]

            if 'auth_key' in query and len(query['auth_key']) > 0:
                auth_key = query['auth_key'][0]

            response_info = ResponseInfo(
                status_code=res.status_code,
                tls_enabled='https' == res.url.scheme,
                origin=res.url.host,
                uuid=uuid,
                auth_key=auth_key,
                client_request=res.request
            )

        if res.status_code not in [200, 204, 307]:
            if res.status_code == 403:
                status_category = PNStatusCategory.PNAccessDeniedCategory

            if res.status_code == 400:
                status_category = PNStatusCategory.PNBadRequestCategory

            if res.text is None:
                text = "N/A"
            else:
                # Safely access response text - handle streaming responses
                try:
                    text = res.text
                except httpx.ResponseNotRead:
                    # For streaming responses, we need to read first
                    text = res.content.decode('utf-8', errors='ignore')
                except Exception:
                    # Fallback in case of any response reading issues
                    text = f"Response content unavailable (status: {res.status_code})"

            if res.status_code >= 500:
                err = PNERR_SERVER_ERROR
            else:
                err = PNERR_CLIENT_ERROR
            try:
                response = res.json()
            except JSONDecodeError:
                response = None
            return Envelope(
                result=None,
                status=e_options.create_status(
                    category=status_category,
                    response=response,
                    response_info=response_info,
                    exception=PubNubException(
                        pn_error=err,
                        errormsg=text,
                        status_code=res.status_code
                    )))
        else:
            if e_options.non_json_response:
                response = res
            else:
                response = res.json()

            return Envelope(
                result=e_options.create_response(response),
                status=e_options.create_status(
                    category=PNStatusCategory.PNAcknowledgmentCategory,
                    response=response,
                    response_info=response_info,
                    exception=None
                )
            )

    def _invoke_request(self, p_options, e_options, base_origin):
        assert isinstance(p_options, PlatformOptions)
        assert isinstance(e_options, RequestOptions)

        session = self._ensure_session()

        if base_origin:
            url = p_options.pn_config.scheme() + "://" + base_origin + e_options.path
        else:
            url = e_options.path

        if e_options.request_headers:
            request_headers = {**p_options.headers, **e_options.request_headers}
        else:
            request_headers = p_options.headers

        args = {
            "method": e_options.method_string,
            "headers": request_headers,
            "url": httpx.URL(url, query=e_options.query_string.encode("utf-8")),
            "timeout": httpx.Timeout(
                connect=e_options.connect_timeout,
                read=e_options.request_timeout,
                write=e_options.connect_timeout,
                pool=e_options.connect_timeout),
            "follow_redirects": e_options.allow_redirects
        }

        if e_options.is_post() or e_options.is_patch():
            args["content"] = e_options.data
            args["files"] = e_options.files
            logger.debug("%s %s %s" % (
                e_options.method_string,
                utils.build_url(
                    p_options.pn_config.scheme(),
                    base_origin,
                    e_options.path,
                    e_options.query_string), e_options.data))
        else:
            logger.debug("%s %s" % (
                e_options.method_string,
                utils.build_url(
                    p_options.pn_config.scheme(),
                    base_origin,
                    e_options.path,
                    e_options.query_string)))

        # Wall-clock deadline: only for long-timeout requests (e.g., subscribe long-poll)
        # where system sleep can cause monotonic-based socket timeouts to stall for hours.
        # Short requests (publish, history, etc.) don't need this.
        use_watchdog = e_options.request_timeout is not None and e_options.request_timeout > 30

        if use_watchdog:
            self._watchdog.set_deadline(session, time.time() + e_options.request_timeout)

        try:
            res = session.request(**args)
            # Safely access response text - read content first for streaming responses
            try:
                logger.debug("GOT %s" % res.text)
            except httpx.ResponseNotRead:
                # For streaming responses, we need to read first
                logger.debug("GOT %s" % res.content.decode('utf-8', errors='ignore'))
            except Exception as e:
                # Fallback logging in case of any response reading issues
                logger.debug("GOT response (content access failed: %s)" % str(e))

        except httpx.ConnectError as e:
            if use_watchdog and self._watchdog.triggered:
                raise PubNubException(
                    pn_error=PNERR_CLIENT_TIMEOUT,
                    errormsg="Wall-clock deadline exceeded (system sleep detected)"
                )
            raise PubNubException(
                pn_error=PNERR_CONNECTION_ERROR,
                errormsg=str(e)
            )
        except httpx.TimeoutException as e:
            if use_watchdog and self._watchdog.triggered:
                raise PubNubException(
                    pn_error=PNERR_CLIENT_TIMEOUT,
                    errormsg="Wall-clock deadline exceeded (system sleep detected)"
                )
            raise PubNubException(
                pn_error=PNERR_CLIENT_TIMEOUT,
                errormsg=str(e)
            )
        except httpx.TooManyRedirects as e:
            raise PubNubException(
                pn_error=PNERR_TOO_MANY_REDIRECTS_ERROR,
                errormsg=str(e)
            )
        except httpx.HTTPStatusError as e:
            raise PubNubException(
                pn_error=PNERR_HTTP_ERROR,
                errormsg=str(e),
                status_code=e.response.status_code
            )
        except Exception as e:
            if use_watchdog and self._watchdog.triggered:
                raise PubNubException(
                    pn_error=PNERR_CLIENT_TIMEOUT,
                    errormsg="Wall-clock deadline exceeded (system sleep detected)"
                )
            raise PubNubException(
                pn_error=PNERR_UNKNOWN_ERROR,
                errormsg=str(e)
            )
        finally:
            if use_watchdog:
                self._watchdog.clear_deadline()

        return res


class AsyncHTTPClient:
    """A wrapper for threaded calls"""

    def __init__(self, callback_to_invoke):
        self._callback_to_invoke = callback_to_invoke

    def run(self):
        self._callback_to_invoke()


class Call(object):
    """
    A platform dependent representation of async PubNub method call
    """

    def __init__(self):
        self.thread = None
        self.cancellation_event = None
        self.is_executed = False
        self.is_canceled = False

    def cancel(self):
        """
        Set Event flag to stop thread on timeout. This will not stop thread immediately, it will stopped
          only after ongoing request will be finished
        :return: nothing
        """
        if self.cancellation_event is not None:
            self.cancellation_event.set()
        self.is_canceled = True

    def join(self):
        if isinstance(self.thread, threading.Thread):
            self.thread.join()

    def executed_cb(self):
        self.is_executed = True
