import copy
import logging
import threading
import requests

# noinspection PyUnresolvedReferences
from six.moves.queue import Queue
from threading import Event

from pubnub.endpoints.presence.heartbeat import Heartbeat
from .endpoints.presence.leave import Leave
from .endpoints.pubsub.subscribe import Subscribe
from .workers import SubscribeMessageWorker
from .pnconfiguration import PNConfiguration
from .managers import SubscriptionManager, PublishSequenceManager
from . import utils
from .structures import RequestOptions, ResponseInfo
from .enums import PNStatusCategory, PNHeartbeatNotificationOptions
from .callbacks import SubscribeCallback
from .errors import PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_UNKNOWN_ERROR, \
    PNERR_TOO_MANY_REDIRECTS_ERROR, PNERR_CLIENT_TIMEOUT, PNERR_HTTP_ERROR, PNERR_CONNECTION_ERROR
from .exceptions import PubNubException
from .pubnub_core import PubNubCore

logger = logging.getLogger("pubnub")


class PubNub(PubNubCore):
    """PubNub Python API"""
    ENTITY_THREAD_COUNTER = 0

    def __init__(self, config):
        assert isinstance(config, PNConfiguration)
        self.session = requests.Session()
        PubNubCore.__init__(self, config)

        if self.config.enable_subscribe:
            self._subscription_manager = NativeSubscriptionManager(self)

        self._publish_sequence_manager = PublishSequenceManager(PubNubCore.MAX_SEQUENCE)

    def sdk_platform(self):
        return ""

    def request_sync(self, options):
        res = self.pn_request(self.session,
                              self.config.scheme_and_host(),
                              self.headers,
                              options,
                              self.config.connect_timeout,
                              self.config.non_subscribe_request_timeout)

        # http error
        if res.status_code != requests.codes.ok:
            if res.text is None:
                text = "N/A"
            else:
                text = res.text

            if res.status_code >= 500:
                err = PNERR_SERVER_ERROR
            else:
                err = PNERR_CLIENT_ERROR

            raise PubNubException(
                pn_error=err,
                errormsg=text,
                status_code=res.status_code
            )

        return res

    def request_async(self, endpoint_name, options, callback, cancellation_event):
        # TODO: Rename to AsyncRequest
        call = Call()

        def success_callback(res):
            status_category = PNStatusCategory.PNUnknownCategory
            response_info = None

            if res is not None:
                url = utils.urlparse(res.url)
                query = utils.parse_qs(url.query)
                uuid = None
                auth_key = None

                if 'uuid' in query and len(query['uuid']) > 0:
                    uuid = query['uuid'][0]

                if 'auth_key' in query and len(query['auth_key']) > 0:
                    auth_key = query['auth_key'][0]

                response_info = ResponseInfo(
                    status_code=res.status_code,
                    tls_enabled='https' == url.scheme,
                    origin=url.hostname,
                    uuid=uuid,
                    auth_key=auth_key,
                    client_request=res.request
                )

            if res.status_code != requests.codes.ok:
                if res.status_code == 403:
                    status_category = PNStatusCategory.PNAccessDeniedCategory

                if res.status_code == 400:
                    status_category = PNStatusCategory.PNBadRequestCategory

                if res.text is None:
                    text = "N/A"
                else:
                    text = res.text

                if res.status_code >= 500:
                    err = PNERR_SERVER_ERROR
                else:
                    err = PNERR_CLIENT_ERROR

                callback(status_category, res.json(), response_info, PubNubException(
                    pn_error=err,
                    errormsg=text,
                    status_code=res.status_code
                ))
                call.executed_cb()
            else:
                callback(PNStatusCategory.PNAcknowledgmentCategory, res.json(), response_info, None)
                call.executed_cb()

        def error_callback(e):
            status_category = PNStatusCategory.PNBadRequestCategory
            # TODO: allow non PN errors

            if not type(e) is PubNubException:
                raise e

            if e._pn_error is PNERR_CONNECTION_ERROR:
                status_category = PNStatusCategory.PNUnexpectedDisconnectCategory
            elif e._pn_error is PNERR_CLIENT_TIMEOUT:
                status_category = PNStatusCategory.PNTimeoutCategory

            callback(status_category, None, None, e)
            call.executed_cb()

        client = AsyncHTTPClient(self,
                                 success_callback,
                                 error_callback,
                                 options,
                                 cancellation_event)

        thread = threading.Thread(
            target=client.run,
            name="EndpointThread-%s-%d" % (endpoint_name, ++PubNub.ENTITY_THREAD_COUNTER)
        )
        thread.setDaemon(True)
        thread.start()

        call.thread = thread
        call.cancellation_event = cancellation_event

        return call

    def stop(self):
        self._subscription_manager.stop()

    def request_deferred(self, options_func):
        raise NotImplementedError

    def request_future(self, *args, **kwargs):
        raise NotImplementedError

    def add_listener(self, listener):
        assert isinstance(listener, SubscribeCallback)
        self._subscription_manager.add_listener(listener)

    def pn_request(self, session, scheme_and_host, headers, options, connect_timeout, read_timeout):
        assert isinstance(options, RequestOptions)
        url = scheme_and_host + options.path

        args = {
            "method": options.method_string,
            'headers': headers,
            "url": url,
            'params': options.query_string,
            'timeout': (connect_timeout, read_timeout)
        }

        if options.is_post():
            args['data'] = options.data
            logger.debug("%s %s %s" % (
                options.method_string,
                utils.build_url(
                    self.config.scheme(),
                    self.config.origin,
                    options.path,
                    options.query_string), options.data))
        else:
            logger.debug("%s %s" % (
                options.method_string,
                utils.build_url(
                    self.config.scheme(),
                    self.config.origin,
                    options.path,
                    options.query_string)))

        # connection error
        try:
            res = session.request(**args)
            logger.debug("GOT %s" % res.text)
        except requests.exceptions.ConnectionError as e:
            raise PubNubException(
                pn_error=PNERR_CONNECTION_ERROR,
                errormsg=str(e)
            )
        except requests.exceptions.HTTPError as e:
            raise PubNubException(
                pn_error=PNERR_HTTP_ERROR,
                errormsg=str(e)
            )
        except requests.exceptions.Timeout as e:
            raise PubNubException(
                pn_error=PNERR_CLIENT_TIMEOUT,
                errormsg=str(e)
            )
        except requests.exceptions.TooManyRedirects as e:
            raise PubNubException(
                pn_error=PNERR_TOO_MANY_REDIRECTS_ERROR,
                errormsg=str(e)
            )
        except Exception as e:
            raise PubNubException(
                pn_error=PNERR_UNKNOWN_ERROR,
                errormsg=str(e)
            )

        return res


class AsyncHTTPClient:
    """A wrapper for threaded calls"""

    def __init__(self, pubnub, success, error, options, cancellation_event):
        self.options = options
        self.success = success
        self.error = error
        self.pubnub = pubnub
        self.cancellation_event = cancellation_event

    def run(self):
        try:
            res = self.pubnub.pn_request(
                self.pubnub.session, self.pubnub.config.scheme_and_host(),
                self.pubnub.headers, self.options,
                self.pubnub.config.connect_timeout,
                self.pubnub.config.non_subscribe_request_timeout)

            if self.cancellation_event is not None and self.cancellation_event.isSet():
                # Since there are no way to affect on ongoing request it's response will be just ignored on cancel call
                return

            self.success(res)
        except PubNubException as e:
            self.error(e)
        except Exception as e:
            # TODO: log the exception
            self.error(PubNubException(
                pn_error=PNERR_UNKNOWN_ERROR,
                errormsg="Exception in request thread: %s" % str(e)
            ))


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


class NativeSubscriptionManager(SubscriptionManager):
    def __init__(self, pubnub_instance):
        self._message_queue = utils.Queue()
        self._consumer_event = threading.Event()
        self._subscribe_call = None
        self._heartbeat_periodic_callback = None
        super(NativeSubscriptionManager, self).__init__(pubnub_instance)

    def _send_leave(self, unsubscribe_operation):
        def leave_callback(result, status):
            self._listener_manager.announce_status(status)

        Leave(self._pubnub) \
            .channels(unsubscribe_operation.channels) \
            .channel_groups(unsubscribe_operation.channel_groups).async(leave_callback)

    def _register_heartbeat_timer(self):
        super(NativeSubscriptionManager, self)._register_heartbeat_timer()

        self._perform_heartbeat_loop()

        self._heartbeat_periodic_callback = NativePeriodicCallback(
            self._perform_heartbeat_loop,
            self._pubnub.config.heartbeat_interval * 1000)

        if not self._should_stop:
            self._heartbeat_periodic_callback.start()

    def _perform_heartbeat_loop(self):
        if self._heartbeat_call is not None:
            # TODO: cancel call
            pass

        state_payload = self._subscription_state.state_payload()
        presence_channels = self._subscription_state.prepare_channel_list(False)
        presence_groups = self._subscription_state.prepare_channel_group_list(False)

        if len(presence_channels) == 0 and len(presence_groups) == 0:
            return

        def heartbeat_callback(raw_result, status):
            heartbeat_verbosity = self._pubnub.config.heartbeat_notification_options
            if status.is_error:
                if heartbeat_verbosity == PNHeartbeatNotificationOptions.ALL or \
                                heartbeat_verbosity == PNHeartbeatNotificationOptions.ALL:
                    self._listener_manager.announce_stateus(status)
            else:
                if heartbeat_verbosity == PNHeartbeatNotificationOptions.ALL:
                    self._listener_manager.announce_stateus(status)

        try:
            (Heartbeat(self._pubnub)
             .channels(presence_channels)
             .channel_groups(presence_groups)
             .state(state_payload)
             .async(heartbeat_callback))
        except Exception as e:
            print("failed", e)

    def _stop_heartbeat_timer(self):
        if self._heartbeat_periodic_callback is not None:
            self._heartbeat_periodic_callback.stop()

    def _set_consumer_event(self):
        self._consumer_event.set()
        self._message_queue_put(None)

    def _message_queue_put(self, message):
        self._message_queue.put(message)

    def reconnect(self):
        self._should_stop = False
        self._start_subscribe_loop()
        self._register_heartbeat_timer()

    def _start_worker(self):
        consumer = NativeSubscribeMessageWorker(self._pubnub, self._listener_manager,
                                                self._message_queue, self._consumer_event)
        self._consumer_thread = threading.Thread(target=consumer.run,
                                                 name="SubscribeMessageWorker")
        self._consumer_thread.start()

    def _start_subscribe_loop(self):
        self._stop_subscribe_loop()

        combined_channels = self._subscription_state.prepare_channel_list(True)
        combined_groups = self._subscription_state.prepare_channel_group_list(True)

        if len(combined_channels) == 0 and len(combined_groups) == 0:
            return

        def callback(raw_result, status):
            """ SubscribeEndpoint callback"""
            if status.is_error():
                if status.category is PNStatusCategory.PNTimeoutCategory and not self._should_stop:
                    self._start_subscribe_loop()
                else:
                    self._listener_manager.announce_status(status)

                return

            self._handle_endpoint_call(raw_result, status)
            self._start_subscribe_loop()

        try:
            self._subscribe_call = Subscribe(self._pubnub) \
                .channels(combined_channels).channel_groups(combined_groups) \
                .timetoken(self._timetoken).region(self._region) \
                .filter_expression(self._pubnub.config.filter_expression) \
                .async(callback)
        except Exception as e:
            print("failed", e)

    def _stop_subscribe_loop(self):
        sc = self._subscribe_call

        if sc is not None and not sc.is_executed and not sc.is_canceled:
            sc.cancel()


class NativePeriodicCallback(object):
    def __init__(self, callback, callback_time):
        self._callback = callback
        self._callback_time = callback_time
        self._running = False
        self._timeout = None

    def start(self):
        self._running = True
        self._schedule_next()

    def stop(self):
        self._running = False
        if self._timeout is not None:
            self._timeout.cancel()
            self._timeout = None

    def _run(self):
        if not self._running:
            return
        try:
            self._callback()
        except Exception:
            # TODO: handle the exception
            pass
        finally:
            self._schedule_next()

    def _schedule_next(self):
        self._timeout = threading.Timer(10.0, self._run)
        self._timeout.start()


class NativeSubscribeMessageWorker(SubscribeMessageWorker):
    def _take_message(self):
        while not self._event.isSet():
            try:
                # TODO: get rid of 1s timeout
                msg = self._queue.get(True, 1)
                if msg is not None:
                    self._process_incoming_payload(msg)
                self._queue.task_done()
            except utils.QueueEmpty:
                continue
            except Exception as e:
                # TODO: move to finally
                self._queue.task_done()
                self._event.set()
                logger.warn("take message interrupted: %s" % str(e))


class SubscribeListener(SubscribeCallback):
    def __init__(self):
        self.connected = False
        self.connected_event = Event()
        self.disconnected_event = Event()
        self.presence_queue = Queue()
        self.message_queue = Queue()

    def status(self, pubnub, status):
        if utils.is_subscribed_event(status) and not self.connected_event.is_set():
            self.connected_event.set()
        elif utils.is_unsubscribed_event(status) and not self.disconnected_event.is_set():
            self.disconnected_event.set()

    def message(self, pubnub, message):
        self.message_queue.put(message)

    def presence(self, pubnub, presence):
        self.presence_queue.put(presence)

    def wait_for_connect(self):
        if not self.connected_event.is_set():
            self.connected_event.wait()
        else:
            raise Exception("the instance is already connected")

    def wait_for_disconnect(self):
        if not self.disconnected_event.is_set():
            self.disconnected_event.wait()
        else:
            raise Exception("the instance is already connected")

    def wait_for_message_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            env = self.message_queue.get()
            self.message_queue.task_done()
            if env.actual_channel in channel_names:
                return env
            else:
                continue

    def wait_for_presence_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            env = self.presence_queue.get()
            self.presence_queue.task_done()
            if env.actual_channel[:-7] in channel_names:
                return env
            else:
                continue


class NonSubscribeListener(object):
    def __init__(self):
        self.result = None
        self.done_event = Event()

    def callback(self, result, status):
        self.result = result
        self.done_event.set()

    def await(self, timeout=5):
        """ Returns False if a timeout happened, otherwise True"""
        return self.done_event.wait(timeout)

    def await_result(self, timeout=5):
        self.await(timeout)
        return self.result

    def await_result_and_reset(self, timeout=5):
        self.await(timeout)
        cp = copy.copy(self.result)
        self.reset()
        return cp

    def reset(self):
        self.result = None
        self.done_event.clear()
