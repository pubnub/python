import json
import logging
import time
import datetime

import math
import six
import tornado.gen
import tornado.httpclient
import tornado.ioloop
from tornado import gen

from tornado import ioloop
from tornado import stack_context
from tornado.concurrent import Future
from tornado.ioloop import PeriodicCallback
from tornado.locks import Event, Semaphore, Lock
from tornado.queues import Queue
from tornado.simple_httpclient import SimpleAsyncHTTPClient

from . import utils
from .models.consumer.common import PNStatus
from .callbacks import SubscribeCallback, ReconnectionCallback
from .endpoints.presence.leave import Leave
from .endpoints.pubsub.subscribe import Subscribe
from .enums import PNStatusCategory, PNHeartbeatNotificationOptions, PNOperationType, PNReconnectionPolicy
from .errors import PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_JSON_DECODING_FAILED, PNERR_CLIENT_TIMEOUT, \
    PNERR_CONNECTION_ERROR
from .exceptions import PubNubException
from .managers import SubscriptionManager, PublishSequenceManager, ReconnectionManager, TelemetryManager
from .pubnub_core import PubNubCore
from .structures import ResponseInfo
from .workers import SubscribeMessageWorker

logger = logging.getLogger("pubnub")

tornado.httpclient.AsyncHTTPClient.configure(SimpleAsyncHTTPClient)


class PubNubTornado(PubNubCore):
    MAX_CLIENTS = 1000

    def stop(self):
        self.ioloop.stop()

    def start(self):
        self.ioloop.start()

    def timeout(self, delay, callback, *args):
        handle = None

        def cancel():
            self.ioloop.remove_timeout(handle)

        def cb():
            if callback is not None:
                callback(*args)

        handle = self.ioloop.add_timeout(time.time() + float(delay), cb)

        return cancel

    def sdk_platform(self):
        return "-Tornado"

    def __init__(self, config, custom_ioloop=None):
        super(PubNubTornado, self).__init__(config)
        self.ioloop = custom_ioloop or ioloop.IOLoop.instance()

        if self.config.enable_subscribe:
            self._subscription_manager = TornadoSubscriptionManager(self)

        self._publish_sequence_manager = TornadoPublishSequenceManager(PubNubCore.MAX_SEQUENCE)

        self.http = tornado.httpclient.AsyncHTTPClient(max_clients=PubNubTornado.MAX_CLIENTS)
        self.id = None

        self.headers = {
            'User-Agent': self.sdk_name,
            'Accept-Encoding': 'utf-8'
        }

        self._telemetry_manager = TornadoTelemetryManager(self.ioloop)

    def request_sync(self, *args):
        raise NotImplementedError

    def request_async(self, *args):
        raise NotImplementedError

    def request_deferred(self, *args):
        raise NotImplementedError

    @tornado.gen.coroutine
    def request_result(self, options_func, cancellation_event):
        try:
            envelope = yield self._request_helper(options_func, cancellation_event)
            raise tornado.gen.Return(envelope.result)
        except PubNubTornadoException as ex:
            raise ex.status.error_data.exception

    @tornado.gen.coroutine
    def request_future(self, options_func, cancellation_event):
        try:
            e = yield self._request_helper(options_func, cancellation_event)
        except PubNubTornadoException as ex:
            e = ex
        except Exception as ex:
            e = PubNubTornadoException(
                result=None,
                status=options_func().create_status(PNStatusCategory.PNUnknownCategory,
                                                    None,
                                                    None,
                                                    ex)
            )

        raise tornado.gen.Return(e)

    # REFACTOR: quickly adjusted to fit the new result() and future() endpoints
    def _request_helper(self, options_func, cancellation_event):
        if cancellation_event is not None:
            assert isinstance(cancellation_event, Event)

        # validate_params()
        options = options_func()

        create_response = options.create_response
        create_status_response = options.create_status

        params_to_merge_in = {}

        if options.operation_type == PNOperationType.PNPublishOperation:
            params_to_merge_in['seqn'] = self._publish_sequence_manager.get_next_sequence()

        options.merge_params_in(params_to_merge_in)

        future = Future()

        url = utils.build_url(self.config.scheme(), self.base_origin,
                              options.path, options.query_string)

        logger.debug("%s %s %s" % (options.method_string, url, options.data))

        if options.method_string == "POST":
            self.headers['Content-type'] = "application/json"

        start_timestamp = time.time()

        request = tornado.httpclient.HTTPRequest(
            url=url,
            method=options.method_string,
            headers=self.headers,
            body=options.data if options.data is not None else None,
            connect_timeout=options.connect_timeout,
            request_timeout=options.request_timeout)

        def response_callback(response):
            if cancellation_event is not None and cancellation_event.is_set():
                return

            body = response.body
            response_info = None
            status_category = PNStatusCategory.PNUnknownCategory
            if response is not None:
                request_url = six.moves.urllib.parse.urlparse(response.effective_url)
                query = six.moves.urllib.parse.parse_qs(request_url.query)
                uuid = None
                auth_key = None

                if 'uuid' in query and len(query['uuid']) > 0:
                    uuid = query['uuid'][0]

                if 'auth_key' in query and len(query['auth_key']) > 0:
                    auth_key = query['auth_key'][0]

                response_info = ResponseInfo(
                    status_code=response.code,
                    tls_enabled='https' == request_url.scheme,
                    origin=request_url.hostname,
                    uuid=uuid,
                    auth_key=auth_key,
                    client_request=response.request
                )

            if body is not None and len(body) > 0:
                try:
                    data = json.loads(body)
                except (ValueError, TypeError):
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except ValueError:
                        tornado_result = PubNubTornadoException(
                            create_response(None),
                            create_status_response(status_category, response, response_info, PubNubException(
                                pn_error=PNERR_JSON_DECODING_FAILED,
                                errormsg='json decode error')
                            )
                        )
                        future.set_exception(tornado_result)
                        return
            else:
                data = "N/A"

            logger.debug(data)

            if response.error is not None:
                if response.code >= 500:
                    err = PNERR_SERVER_ERROR
                    data = str(response.error)
                else:
                    err = PNERR_CLIENT_ERROR

                e = PubNubException(
                    errormsg=data,
                    pn_error=err,
                    status_code=response.code,
                )

                if response.code == 403:
                    status_category = PNStatusCategory.PNAccessDeniedCategory

                if response.code == 400:
                    status_category = PNStatusCategory.PNBadRequestCategory

                if response.code == 599:
                    if 'HTTP 599: Timeout during request' == data:
                        status_category = PNStatusCategory.PNTimeoutCategory
                        e = PubNubException(
                            pn_error=PNERR_CLIENT_TIMEOUT,
                            errormsg=str(e)
                        )
                    elif 'HTTP 599: Stream closed' == data or\
                            'Name or service not known' in data or\
                            'Temporary failure in name resolution' in data:
                        status_category = PNStatusCategory.PNNetworkIssuesCategory
                        e = PubNubException(
                            pn_error=PNERR_CONNECTION_ERROR,
                            errormsg=str(e)
                        )
                        # TODO: add check for other status codes

                future.set_exception(PubNubTornadoException(
                    result=data,
                    status=create_status_response(status_category, data, response_info, e)
                ))
            else:
                self._telemetry_manager.store_latency(time.time() - start_timestamp, options.operation_type)

                future.set_result(TornadoEnvelope(
                    result=create_response(data),
                    status=create_status_response(
                        PNStatusCategory.PNAcknowledgmentCategory,
                        data,
                        response_info,
                        None)
                ))

        self.http.fetch(
            request=request,
            callback=response_callback
        )

        return future


class TornadoReconnectionManager(ReconnectionManager):
    def __init__(self, pubnub):
        self._cancelled_event = Event()
        super(TornadoReconnectionManager, self).__init__(pubnub)

    @gen.coroutine
    def _register_heartbeat_timer(self):
        self._cancelled_event.clear()

        while not self._cancelled_event.is_set():
            if self._pubnub.config.reconnect_policy == PNReconnectionPolicy.EXPONENTIAL:
                self._timer_interval = int(math.pow(2, self._connection_errors) - 1)
                if self._timer_interval > self.MAXEXPONENTIALBACKOFF:
                    self._timer_interval = self.MINEXPONENTIALBACKOFF
                    self._connection_errors = 1
                    logger.debug("timerInterval > MAXEXPONENTIALBACKOFF at: %s" % utils.datetime_now())
                elif self._timer_interval < 1:
                    self._timer_interval = self.MINEXPONENTIALBACKOFF
                logger.debug("timerInterval = %d at: %s" % (self._timer_interval, utils.datetime_now()))
            else:
                self._timer_interval = self.INTERVAL

            # >>> Wait given interval or cancel
            sleeper = tornado.gen.sleep(self._timer_interval)
            canceller = self._cancelled_event.wait()

            wi = tornado.gen.WaitIterator(canceller, sleeper)

            while not wi.done():
                try:
                    future = wi.next()
                    yield future
                except Exception as e:
                    # TODO: verify the error will not be eaten
                    logger.error(e)
                    raise
                else:
                    if wi.current_future == sleeper:
                        break
                    elif wi.current_future == canceller:
                        return
                    else:
                        raise Exception("unknown future raised")

            logger.debug("reconnect loop at: %s" % utils.datetime_now())

            # >>> Attempt to request /time/0 endpoint
            try:
                yield self._pubnub.time().result()
                self._connection_errors = 1
                self._callback.on_reconnect()
                logger.debug("reconnection manager stop due success time endpoint call: %s" % utils.datetime_now())
                break
            except Exception:
                if self._pubnub.config.reconnect_policy == PNReconnectionPolicy.EXPONENTIAL:
                    logger.debug("reconnect interval increment at: %s" % utils.datetime_now())
                    self._connection_errors += 1

    def start_polling(self):
        if self._pubnub.config.reconnect_policy == PNReconnectionPolicy.NONE:
            logger.warning("reconnection policy is disabled, please handle reconnection manually.")
            return

        self._pubnub.ioloop.spawn_callback(self._register_heartbeat_timer)

    def stop_polling(self):
        if self._cancelled_event is not None and not self._cancelled_event.is_set():
            self._cancelled_event.set()


class TornadoPublishSequenceManager(PublishSequenceManager):
    def __init__(self, provided_max_sequence):
        super(TornadoPublishSequenceManager, self).__init__(provided_max_sequence)
        self._lock = Lock()
        self._ioloop = ioloop

    def get_next_sequence(self):
        if self.max_sequence == self.next_sequence:
            self.next_sequence = 1
        else:
            self.next_sequence += 1

        return self.next_sequence


class TornadoSubscribeMessageWorker(SubscribeMessageWorker):
    @tornado.gen.coroutine
    def run(self):
        self._take_message()

    @tornado.gen.coroutine
    def _take_message(self):
        i = 0
        while not self._event.is_set():
            try:
                msg = yield self._queue.get(datetime.timedelta(seconds=1))
                if msg is not None:
                    self._process_incoming_payload(msg)
                self._queue.task_done()
            except tornado.gen.TimeoutError:
                i += 1
                continue


class TornadoSubscriptionManager(SubscriptionManager):
    def __init__(self, pubnub_instance):

        subscription_manager = self

        self._message_queue = Queue()
        self._consumer_event = Event()
        self._cancellation_event = Event()
        self._subscription_lock = Semaphore(1)
        # self._current_request_key_object = None
        self._heartbeat_periodic_callback = None
        self._reconnection_manager = TornadoReconnectionManager(pubnub_instance)

        super(TornadoSubscriptionManager, self).__init__(pubnub_instance)
        self._start_worker()

        class TornadoReconnectionCallback(ReconnectionCallback):
            def on_reconnect(self):
                subscription_manager.reconnect()

                pn_status = PNStatus()
                pn_status.category = PNStatusCategory.PNReconnectedCategory
                pn_status.error = False

                subscription_manager._subscription_status_announced = True
                subscription_manager._listener_manager.announce_status(pn_status)

        self._reconnection_listener = TornadoReconnectionCallback()
        self._reconnection_manager.set_reconnection_listener(self._reconnection_listener)

    def _set_consumer_event(self):
        self._consumer_event.set()

    def _message_queue_put(self, message):
        self._message_queue.put(message)

    def _start_worker(self):
        self._consumer = TornadoSubscribeMessageWorker(self._pubnub,
                                                       self._listener_manager,
                                                       self._message_queue,
                                                       self._consumer_event)
        run = stack_context.wrap(self._consumer.run)
        self._pubnub.ioloop.spawn_callback(run)

    def reconnect(self):
        self._should_stop = False
        self._pubnub.ioloop.spawn_callback(self._start_subscribe_loop)
        # self._register_heartbeat_timer()

    def disconnect(self):
        self._should_stop = True
        self._stop_heartbeat_timer()
        self._stop_subscribe_loop()

    @tornado.gen.coroutine
    def _start_subscribe_loop(self):
        self._stop_subscribe_loop()

        yield self._subscription_lock.acquire()

        self._cancellation_event.clear()

        combined_channels = self._subscription_state.prepare_channel_list(True)
        combined_groups = self._subscription_state.prepare_channel_group_list(True)

        if len(combined_channels) == 0 and len(combined_groups) == 0:
            return

        envelope_future = Subscribe(self._pubnub) \
            .channels(combined_channels).channel_groups(combined_groups) \
            .timetoken(self._timetoken).region(self._region) \
            .filter_expression(self._pubnub.config.filter_expression) \
            .cancellation_event(self._cancellation_event) \
            .future()

        canceller_future = self._cancellation_event.wait()

        wi = tornado.gen.WaitIterator(envelope_future, canceller_future)

        # iterates 2 times: one for result one for cancelled
        while not wi.done():
            try:
                result = yield wi.next()
            except Exception as e:
                # TODO: verify the error will not be eaten
                logger.error(e)
                raise
            else:
                if wi.current_future == envelope_future:
                    e = result
                elif wi.current_future == canceller_future:
                    return
                else:
                    raise Exception("Unexpected future resolved: %s" % str(wi.current_future))

                if e.is_error():
                    # 599 error doesn't works - tornado use this status code
                    # for a wide range of errors, for ex:
                    # HTTP Server Error (599): [Errno -2] Name or service not known
                    if e.status is not None and e.status.category == PNStatusCategory.PNTimeoutCategory:
                        self._pubnub.ioloop.spawn_callback(self._start_subscribe_loop)
                        return

                    logger.error("Exception in subscribe loop: %s" % str(e))

                    if e.status is not None and e.status.category == PNStatusCategory.PNAccessDeniedCategory:
                        e.status.operation = PNOperationType.PNUnsubscribeOperation

                    self._listener_manager.announce_status(e.status)

                    self._reconnection_manager.start_polling()
                    self.disconnect()
                    return
                else:
                    self._handle_endpoint_call(e.result, e.status)

                    self._pubnub.ioloop.spawn_callback(self._start_subscribe_loop)

            finally:
                self._cancellation_event.set()
                yield tornado.gen.moment
                self._subscription_lock.release()
                self._cancellation_event.clear()
                break

    def _stop_subscribe_loop(self):
        if self._cancellation_event is not None and not self._cancellation_event.is_set():
            self._cancellation_event.set()

    def _stop_heartbeat_timer(self):
        if self._heartbeat_periodic_callback is not None:
            self._heartbeat_periodic_callback.stop()

    def _register_heartbeat_timer(self):
        super(TornadoSubscriptionManager, self)._register_heartbeat_timer()
        self._heartbeat_periodic_callback = PeriodicCallback(
            stack_context.wrap(self._perform_heartbeat_loop),
            self._pubnub.config.heartbeat_interval * TornadoSubscriptionManager.HEARTBEAT_INTERVAL_MULTIPLIER,
            self._pubnub.ioloop)
        self._heartbeat_periodic_callback.start()

    @tornado.gen.coroutine
    def _perform_heartbeat_loop(self):
        if self._heartbeat_call is not None:
            # TODO: cancel call
            pass

        cancellation_event = Event()
        state_payload = self._subscription_state.state_payload()
        presence_channels = self._subscription_state.prepare_channel_list(False)
        presence_groups = self._subscription_state.prepare_channel_group_list(False)

        if len(presence_channels) == 0 and len(presence_groups) == 0:
            return

        try:
            envelope = yield self._pubnub.heartbeat() \
                .channels(presence_channels) \
                .channel_groups(presence_groups) \
                .state(state_payload) \
                .cancellation_event(cancellation_event) \
                .future()

            heartbeat_verbosity = self._pubnub.config.heartbeat_notification_options
            if envelope.status.is_error:
                if heartbeat_verbosity == PNHeartbeatNotificationOptions.ALL or \
                        heartbeat_verbosity == PNHeartbeatNotificationOptions.ALL:
                    self._listener_manager.announce_status(envelope.status)
            else:
                if heartbeat_verbosity == PNHeartbeatNotificationOptions.ALL:
                    self._listener_manager.announce_status(envelope.status)

        except PubNubTornadoException:
            pass
            # TODO: check correctness
            # if e.status is not None and e.status.category == PNStatusCategory.PNTimeoutCategory:
            #     self._start_subscribe_loop()
            # else:
            #     self._listener_manager.announce_status(e.status)
        except Exception as e:
            print(e)
        finally:
            cancellation_event.set()

    @tornado.gen.coroutine
    def _send_leave(self, unsubscribe_operation):
        envelope = yield Leave(self._pubnub) \
            .channels(unsubscribe_operation.channels) \
            .channel_groups(unsubscribe_operation.channel_groups).future()
        self._listener_manager.announce_status(envelope.status)


class TornadoEnvelope(object):
    def __init__(self, result, status):
        self.result = result
        self.status = status

    @staticmethod
    def is_error():
        return False


class PubNubTornadoException(Exception):
    def __init__(self, result, status):
        self.result = result
        self.status = status

    def __str__(self):
        return str(self.status.error_data.exception)

    @staticmethod
    def is_error():
        return True

    def value(self):
        return self.status.error_data.exception


class SubscribeListener(SubscribeCallback):
    def __init__(self):
        self.connected = False
        self.connected_event = Event()
        self.disconnected_event = Event()
        self.presence_queue = Queue()
        self.message_queue = Queue()
        self.error_queue = Queue()

    def status(self, pubnub, status):
        if utils.is_subscribed_event(status) and not self.connected_event.is_set():
            self.connected_event.set()
        elif utils.is_unsubscribed_event(status) and not self.disconnected_event.is_set():
            self.disconnected_event.set()
        elif status.is_error():
            self.error_queue.put_nowait(status.error_data.exception)

    def message(self, pubnub, message):
        self.message_queue.put(message)

    def presence(self, pubnub, presence):
        self.presence_queue.put(presence)

    @tornado.gen.coroutine
    def _wait_for(self, coro):
        error = self.error_queue.get()
        wi = tornado.gen.WaitIterator(coro, error)

        while not wi.done():
            result = yield wi.next()

            if wi.current_future == coro:
                raise gen.Return(result)
            elif wi.current_future == error:
                raise result
            else:
                raise Exception("Unexpected future resolved: %s" % str(wi.current_future))

    @tornado.gen.coroutine
    def wait_for_connect(self):
        if not self.connected_event.is_set():
            yield self._wait_for(self.connected_event.wait())
        else:
            raise Exception("instance is already connected")

    @tornado.gen.coroutine
    def wait_for_disconnect(self):
        if not self.disconnected_event.is_set():
            yield self._wait_for(self.disconnected_event.wait())
        else:
            raise Exception("instance is already disconnected")

    @tornado.gen.coroutine
    def wait_for_message_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            try:  # NOQA
                env = yield self._wait_for(self.message_queue.get())
                if env.channel in channel_names:
                    raise tornado.gen.Return(env)
                else:
                    continue
            finally:
                self.message_queue.task_done()

    @tornado.gen.coroutine
    def wait_for_presence_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            try:
                try:
                    env = yield self._wait_for(self.presence_queue.get())
                except:  # NOQA E722 pylint: disable=W0702
                    break
                if env.channel in channel_names:
                    raise tornado.gen.Return(env)
                else:
                    continue
            finally:
                self.presence_queue.task_done()


class TornadoTelemetryManager(TelemetryManager):  # pylint: disable=W0612
    def __init__(self, ioloop):
        TelemetryManager.__init__(self)
        self.ioloop = ioloop
        self._timer = PeriodicCallback(
            stack_context.wrap(self._start_clean_up_timer),
            self.CLEAN_UP_INTERVAL * self.CLEAN_UP_INTERVAL_MULTIPLIER,
            self.ioloop)
        self._timer.start()

    @tornado.gen.coroutine
    def _start_clean_up_timer(self):
        self.clean_up_telemetry_data()

    def _stop_clean_up_timer(self):
        self._timer.stop()
