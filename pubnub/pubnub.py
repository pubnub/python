import copy
import logging
import threading

from threading import Event
from queue import Queue, Empty

from . import utils
from .request_handlers.base import BaseRequestHandler
from .request_handlers.requests_handler import RequestsRequestHandler
from .callbacks import SubscribeCallback, ReconnectionCallback
from .endpoints.presence.heartbeat import Heartbeat
from .endpoints.presence.leave import Leave
from .endpoints.pubsub.subscribe import Subscribe
from .enums import PNStatusCategory, PNHeartbeatNotificationOptions, PNOperationType, PNReconnectionPolicy
from .managers import SubscriptionManager, PublishSequenceManager, ReconnectionManager, TelemetryManager
from .models.consumer.common import PNStatus
from .pnconfiguration import PNConfiguration
from .pubnub_core import PubNubCore
from .structures import PlatformOptions
from .workers import SubscribeMessageWorker

logger = logging.getLogger("pubnub")


class PubNub(PubNubCore):
    """PubNub Python API"""

    def __init__(self, config):
        assert isinstance(config, PNConfiguration)

        self._request_handler = RequestsRequestHandler(self)
        PubNubCore.__init__(self, config)

        if self.config.enable_subscribe:
            self._subscription_manager = NativeSubscriptionManager(self)

        self._publish_sequence_manager = PublishSequenceManager(PubNubCore.MAX_SEQUENCE)

        self._telemetry_manager = NativeTelemetryManager()

    def sdk_platform(self):
        return ""

    def set_request_handler(self, handler):
        assert isinstance(handler, BaseRequestHandler)
        self._request_handler = handler

    def request_sync(self, endpoint_call_options):
        platform_options = PlatformOptions(self.headers, self.config)

        self.merge_in_params(endpoint_call_options)

        if self.config.log_verbosity:
            print(endpoint_call_options)

        return self._request_handler.sync_request(platform_options, endpoint_call_options)

    def request_async(self, endpoint_name, endpoint_call_options, callback, cancellation_event):
        platform_options = PlatformOptions(self.headers, self.config)

        self.merge_in_params(endpoint_call_options)

        if self.config.log_verbosity:
            print(endpoint_call_options)

        return self._request_handler.async_request(
            endpoint_name,
            platform_options,
            endpoint_call_options,
            callback,
            cancellation_event
        )

    def merge_in_params(self, options):

        params_to_merge_in = {}

        if options.operation_type == PNOperationType.PNPublishOperation:
            params_to_merge_in['seqn'] = self._publish_sequence_manager.get_next_sequence()

        options.merge_params_in(params_to_merge_in)

    def stop(self):
        if self._subscription_manager is not None:
            self._subscription_manager.stop()
        else:
            raise Exception("Subscription manager is not enabled for this instance")

    def request_deferred(self, options_func):
        raise NotImplementedError

    def request_future(self, *args, **kwargs):
        raise NotImplementedError


class NativeReconnectionManager(ReconnectionManager):
    def __init__(self, pubnub):
        super(NativeReconnectionManager, self).__init__(pubnub)

    def _register_heartbeat_timer(self):
        self.stop_heartbeat_timer()

        self._recalculate_interval()

        self._timer = threading.Timer(self._timer_interval, self._call_time)
        self._timer.setDaemon(True)
        self._timer.start()

    def _call_time(self):
        self._pubnub.time().pn_async(self._call_time_callback)

    def _call_time_callback(self, resp, status):
        if not status.is_error():
            self._connection_errors = 1
            self.stop_heartbeat_timer()
            self._callback.on_reconnect()
            logger.debug("reconnection manager stop due success time endpoint call: %s" % utils.datetime_now())
        elif self._pubnub.config.reconnect_policy == PNReconnectionPolicy.EXPONENTIAL:
            logger.debug("reconnect interval increment at: %s" % utils.datetime_now())
            self.stop_heartbeat_timer()
            self._connection_errors += 1
            self._register_heartbeat_timer()
        elif self._pubnub.config.reconnect_policy == PNReconnectionPolicy.LINEAR:
            self.stop_heartbeat_timer()
            self._connection_errors += 1
            self._register_heartbeat_timer()

    def start_polling(self):
        if self._pubnub.config.reconnect_policy == PNReconnectionPolicy.NONE:
            logger.warning("reconnection policy is disabled, please handle reconnection manually.")
            return

        logger.debug("reconnection manager start at: %s" % utils.datetime_now())

        self._register_heartbeat_timer()

    def stop_heartbeat_timer(self):
        if self._timer is not None:
            self._timer.cancel()


class NativePublishSequenceManager(PublishSequenceManager):
    def __init__(self, provided_max_sequence):
        super(NativePublishSequenceManager, self).__init__(provided_max_sequence)
        self._lock = threading.Lock()

    def get_next_sequence(self):
        with self._lock:
            if self.max_sequence == self.next_sequence:
                self.next_sequence = 1
            else:
                self.next_sequence += 1

            return self.next_sequence


class NativeSubscriptionManager(SubscriptionManager):
    def __init__(self, pubnub_instance):
        subscription_manager = self

        self._message_queue = Queue()
        self._consumer_event = threading.Event()
        self._subscribe_call = None
        self._heartbeat_periodic_callback = None
        self._reconnection_manager = NativeReconnectionManager(pubnub_instance)

        super(NativeSubscriptionManager, self).__init__(pubnub_instance)
        self._start_worker()

        class NativeReconnectionCallback(ReconnectionCallback):
            def on_reconnect(self):
                subscription_manager.reconnect()

                pn_status = PNStatus()
                pn_status.category = PNStatusCategory.PNReconnectedCategory
                pn_status.error = False

                subscription_manager._subscription_status_announced = True
                subscription_manager._listener_manager.announce_status(pn_status)

        self._reconnection_listener = NativeReconnectionCallback()
        self._reconnection_manager.set_reconnection_listener(self._reconnection_listener)

    def _send_leave(self, unsubscribe_operation):
        def leave_callback(result, status):
            self._listener_manager.announce_status(status)

        Leave(self._pubnub) \
            .channels(unsubscribe_operation.channels) \
            .channel_groups(unsubscribe_operation.channel_groups).pn_async(leave_callback)

    def _register_heartbeat_timer(self):
        super(NativeSubscriptionManager, self)._register_heartbeat_timer()

        self._perform_heartbeat_loop()

        self._heartbeat_periodic_callback = NativePeriodicCallback(
            self._perform_heartbeat_loop,
            self._pubnub.config.heartbeat_interval)

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
                    self._listener_manager.announce_status(status)
            else:
                if heartbeat_verbosity == PNHeartbeatNotificationOptions.ALL:
                    self._listener_manager.announce_status(status)

        try:
            (Heartbeat(self._pubnub)
             .channels(presence_channels)
             .channel_groups(presence_groups)
             .state(state_payload)
             .pn_async(heartbeat_callback))
        except Exception as e:
            logger.error("Heartbeat request failed: %s" % e)

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
        # Check the instance flag to determine if we want to perform the presence heartbeat
        # This is False by default
        if self._pubnub.config.enable_presence_heartbeat is True:
            self._register_heartbeat_timer()

    def disconnect(self):
        self._should_stop = True
        self._stop_heartbeat_timer()
        self._stop_subscribe_loop()

    def _start_worker(self):
        consumer = NativeSubscribeMessageWorker(self._pubnub, self._listener_manager,
                                                self._message_queue, self._consumer_event)
        self._consumer_thread = threading.Thread(target=consumer.run,
                                                 name="SubscribeMessageWorker")
        self._consumer_thread.setDaemon(True)
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
                if status is not None and status.category == PNStatusCategory.PNCancelledCategory:
                    return

                if status.category is PNStatusCategory.PNTimeoutCategory and not self._should_stop:
                    self._start_subscribe_loop()
                    return

                logger.error("Exception in subscribe loop: %s" % str(status.error_data.exception))

                if status is not None and status.category == PNStatusCategory.PNAccessDeniedCategory:
                    status.operation = PNOperationType.PNUnsubscribeOperation
                    self._listener_manager.announce_status(status)
                    self.unsubscribe_all()
                    self.disconnect()
                    return

                self._listener_manager.announce_status(status)
                self._reconnection_manager.start_polling()
                self.disconnect()
            else:
                self._handle_endpoint_call(raw_result, status)
                self._start_subscribe_loop()

        try:
            self._subscribe_call = Subscribe(self._pubnub) \
                .channels(combined_channels).channel_groups(combined_groups) \
                .timetoken(self._timetoken).region(self._region) \
                .filter_expression(self._pubnub.config.filter_expression) \
                .pn_async(callback)
        except Exception as e:
            logger.error("Subscribe request failed: %s" % e)

    def _stop_subscribe_loop(self):
        sc = self._subscribe_call

        if sc is not None and not sc.is_executed and not sc.is_canceled:
            sc.cancel()


class NativePeriodicCallback:
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
        self._timeout = threading.Timer(self._callback_time, self._run)
        self._timeout.setDaemon(True)
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
            except Empty:
                continue
            except Exception as e:
                # TODO: move to finally
                self._queue.task_done()
                self._event.set()
                logger.error("take message interrupted: %s" % str(e))
                raise


class SubscribeListener(SubscribeCallback):
    def __init__(self):
        self.connected = False
        self.connected_event = Event()
        self.disconnected_event = Event()
        self.presence_queue = Queue()
        self.message_queue = Queue()
        self.channel_queue = Queue()
        self.uuid_queue = Queue()
        self.membership_queue = Queue()

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

    def channel(self, pubnub, channel):
        self.channel_queue.put(channel)

    def uuid(self, pubnub, uuid):
        self.uuid_queue.put(uuid)

    def membership(self, pubnub, membership):
        self.membership_queue.put(membership)

    def wait_for_disconnect(self):
        if not self.disconnected_event.is_set():
            self.disconnected_event.wait()
        else:
            raise Exception("the instance is already disconnected")

    def wait_for_message_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            env = self.message_queue.get()
            self.message_queue.task_done()
            if env.channel in channel_names:
                return env
            else:
                continue

    def wait_for_presence_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            env = self.presence_queue.get()
            self.presence_queue.task_done()
            if env.channel in channel_names:
                return env
            else:
                continue


class NonSubscribeListener:
    def __init__(self):
        self.result = None
        self.status = None
        self.done_event = Event()

    def callback(self, result, status):
        self.result = result
        self.status = status
        self.done_event.set()

    def pn_await(self, timeout=5):
        """ Returns False if a timeout happened, otherwise True"""
        return self.done_event.wait(timeout)

    def await_result(self, timeout=5):
        self.pn_await(timeout)
        return self.result

    def await_result_and_reset(self, timeout=5):
        self.pn_await(timeout)
        cp = copy.copy(self.result)
        self.reset()
        return cp

    def reset(self):
        self.result = None
        self.status = None
        self.done_event.clear()


class NativeTelemetryManager(TelemetryManager):  # pylint: disable=W0612
    def store_latency(self, latency, operation_type):
        super(NativeTelemetryManager, self).store_latency(latency, operation_type)
        self.clean_up_telemetry_data()
