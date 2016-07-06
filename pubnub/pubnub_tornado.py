import functools
import json
import logging
import time
import datetime

import tornado.gen
import tornado.httpclient
import tornado.ioloop
from tornado import ioloop
from tornado import stack_context
from tornado.concurrent import Future
from tornado.ioloop import PeriodicCallback
from tornado.locks import Event, Semaphore
from tornado.log import gen_log
from tornado.queues import Queue
from tornado.simple_httpclient import SimpleAsyncHTTPClient

from . import utils
from .callbacks import SubscribeCallback
from .endpoints.presence.leave import Leave
from .endpoints.pubsub.subscribe import Subscribe
from .enums import PNStatusCategory, PNHeartbeatNotificationOptions
from .errors import PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_JSON_DECODING_FAILED
from .exceptions import PubNubException
from .managers import SubscriptionManager, PublishSequenceManager
from .pubnub_core import PubNubCore
from .structures import ResponseInfo
from .workers import SubscribeMessageWorker

logger = logging.getLogger("pubnub")


class TornadoCurlAsyncHTTPClient(SimpleAsyncHTTPClient):
    def reset_request(self, key_object):
        if key_object in self.waiting:
            self.io_loop.add_callback(self._on_timeout, key_object)

    def fetch_impl(self, request, initial_callback):
        key = object()

        def after_key_callback(callback):
            self.queue.append((key, request, callback))
            if not len(self.active) < self.max_clients:
                timeout_handle = self.io_loop.add_timeout(
                    self.io_loop.time() + min(request.connect_timeout,
                                              request.request_timeout),
                    functools.partial(self._on_timeout, key))
            else:
                timeout_handle = None
            self.waiting[key] = (request, callback, timeout_handle)
            self._process_queue()
            if self.queue:
                gen_log.debug("max_clients limit reached, request queued. "
                              "%d active, %d queued requests." % (
                                  len(self.active), len(self.queue)))

        self.io_loop.add_callback(initial_callback, _TornadoKeyResponse(key, after_key_callback))


class _TornadoKeyResponse(object):
    def __init__(self, key, after_key_callback):
        self.error = None
        self.key = key
        self.continue_callback = after_key_callback


tornado.httpclient.AsyncHTTPClient.configure(TornadoCurlAsyncHTTPClient)


class PubNubTornado(PubNubCore):
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

    # TODO: deprecate
    def set_ioloop(self, ioloop):
        self.ioloop = ioloop

    def sdk_platform(self):
        return "-Tornado"

    def __init__(self, config, custom_ioloop=None):
        super(PubNubTornado, self).__init__(config)
        self.ioloop = custom_ioloop or ioloop.IOLoop.instance()

        if self.config.enable_subscribe:
            self._subscription_manager = TornadoSubscriptionManager(self)

        # TODO: replace with platform-specific manager
        self._publish_sequence_manager = PublishSequenceManager(PubNubCore.MAX_SEQUENCE)
        # TODO: choose a correct client here http://www.tornadoweb.org/en/stable/httpclient.html
        # TODO: 1000?
        self.http = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
        self.id = None
        # TODO: add accept encoding should be configurable
        self.headers = {
            'User-Agent': self.sdk_name,
            'Accept-Encoding': 'utf-8'
        }

    def add_listener(self, listener):
        if self._subscription_manager is not None:
            self._subscription_manager.add_listener(listener)
        else:
            raise Exception("Subscription manager is not enabled for this instance")

    # TODO: extract this into a separate class
    def request_sync(self, *args):
        raise NotImplementedError

    def request_async(self, *args):
        raise NotImplementedError

    def request_deferred(self, *args):
        raise NotImplementedError

    def request_future(self, intermediate_key_future, options_func,
                       create_response, create_status_response, cancellation_event):
        key_future = self.request_future_key(options_func,
                                             create_response,
                                             create_status_response,
                                             cancellation_event)
        if intermediate_key_future:
            return key_future
        else:
            @tornado.gen.coroutine
            def cb():
                key, call = yield key_future
                blah = yield call
                raise tornado.gen.Return(blah)

            return cb()

    def request_future_key(self, options_func, create_response,
                           create_status_response, cancellation_event):
        if cancellation_event is not None:
            assert isinstance(cancellation_event, Event)

        options = options_func()
        key_future = Future()

        url = utils.build_url(self.config.scheme(), self.config.origin,
                              options.path, options.query_string)
        logger.debug("%s %s %s" % (options.method_string, url, options.data))

        request = tornado.httpclient.HTTPRequest(
            url=url,
            method=options.method_string,
            headers=self.headers,
            body=options.data if options.data is not None else None,
            connect_timeout=options.connect_timeout,
            request_timeout=options.request_timeout)

        def key_callback(key_response):
            future = Future()
            key_future.set_result((key_response.key, future))

            def response_callback(response):
                if cancellation_event is not None and cancellation_event.is_set():
                    return

                body = response.body
                response_info = None
                status_category = PNStatusCategory.PNUnknownCategory

                if response is not None:
                    request_url = utils.urlparse(response.effective_url)
                    query = utils.parse_qs(request_url.query)
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
                    except TypeError:
                        try:
                            data = json.loads(body.decode("utf-8"))
                        except ValueError:
                            tornado_result = TornadoEnvelope(
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
                    else:
                        err = PNERR_CLIENT_ERROR

                    if response.code == 403:
                        status_category = PNStatusCategory.PNAccessDeniedCategory

                    if response.code == 400:
                        status_category = PNStatusCategory.PNBadRequestCategory

                    if response.code == 599:
                        status_category = PNStatusCategory.PNTimeoutCategory

                    future.set_exception(PubNubTornadoException(
                        result=data,
                        status=create_status_response(status_category, data, response_info,
                                                      PubNubException(
                                                          errormsg=data,
                                                          pn_error=err,
                                                          status_code=response.code,
                                                      ))
                    ))
                else:
                    future.set_result(TornadoEnvelope(
                        result=create_response(data),
                        status=create_status_response(
                            PNStatusCategory.PNAcknowledgmentCategory,
                            data,
                            response_info,
                            None)
                    ))

            key_response.continue_callback(response_callback)

        self.http.fetch(
            request=request,
            callback=key_callback
        )

        return key_future


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
        self._message_queue = Queue()
        self._consumer_event = Event()
        self._subscription_lock = Semaphore(1)
        self._current_request_key_object = None
        self._heartbeat_periodic_callback = None
        super(TornadoSubscriptionManager, self).__init__(pubnub_instance)

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
        self._pubnub.ioloop.add_callback(self._start_subscribe_loop)
        self._register_heartbeat_timer()

    @tornado.gen.coroutine
    def _start_subscribe_loop(self):
        self._stop_subscribe_loop()
        yield self._subscription_lock.acquire()
        cancellation_event = Event()

        combined_channels = self._subscription_state.prepare_channel_list(True)
        combined_groups = self._subscription_state.prepare_channel_group_list(True)

        if len(combined_channels) == 0 and len(combined_groups) == 0:
            return

        try:
            key_object, subscribe = yield Subscribe(self._pubnub) \
                .channels(combined_channels).channel_groups(combined_groups) \
                .timetoken(self._timetoken).region(self._region) \
                .filter_expression(self._pubnub.config.filter_expression) \
                .cancellation_event(cancellation_event) \
                .future(intermediate_key_future=True)

            self._current_request_key_object = key_object
            envelope = yield subscribe

            self._handle_endpoint_call(envelope.result, envelope.status)
            self._start_subscribe_loop()
        except PubNubTornadoException as e:
            if e.status is not None and e.status.category == PNStatusCategory.PNTimeoutCategory:
                self._pubnub.ioloop.add_callback(self._start_subscribe_loop)
            else:
                self._listener_manager.announce_status(e.status)
        finally:
            cancellation_event.set()
            self._subscription_lock.release()

    def _stop_subscribe_loop(self):
        self._pubnub.http.reset_request(self._current_request_key_object)

    def _stop_heartbeat_timer(self):
        if self._heartbeat_periodic_callback is not None:
            self._heartbeat_periodic_callback.stop()

    def _register_heartbeat_timer(self):
        super(TornadoSubscriptionManager, self)._register_heartbeat_timer()

        self._heartbeat_periodic_callback = PeriodicCallback(
            stack_context.wrap(self._perform_heartbeat_loop),
            self._pubnub.config.heartbeat_interval *
            TornadoSubscriptionManager.HEARTBEAT_INTERVAL_MULTIPLIER,
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
                    self._listener_manager.announce_stateus(envelope.status)
            else:
                if heartbeat_verbosity == PNHeartbeatNotificationOptions.ALL:
                    self._listener_manager.announce_stateus(envelope.status)

        except PubNubTornadoException as e:
            pass
            # if e.status is not None and e.status.category == PNStatusCategory.PNTimeoutCategory:
            #     self._start_subscribe_loop()
            # else:
            #     self._listener_manager.announce_status(e.status)
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


class PubNubTornadoException(Exception):
    def __init__(self, result, status):
        self.result = result
        self.status = status

    def __str__(self):
        return str(self.status.error_data.exception)


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

    @tornado.gen.coroutine
    def wait_for_connect(self):
        if not self.connected_event.is_set():
            yield self.connected_event.wait()
        else:
            raise Exception("instance is already connected")

    @tornado.gen.coroutine
    def wait_for_disconnect(self):
        if not self.disconnected_event.is_set():
            yield self.disconnected_event.wait()
        else:
            raise Exception("instance is already disconnected")

    @tornado.gen.coroutine
    def wait_for_message_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            try:
                env = yield self.message_queue.get()
                if env.actual_channel in channel_names:
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
                env = yield self.presence_queue.get()
                if env.actual_channel[:-7] in channel_names:
                    raise tornado.gen.Return(env)
                else:
                    continue
            finally:
                self.presence_queue.task_done()
