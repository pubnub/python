"""PubNub Python SDK Implementation.

This module provides the main implementation of the PubNub Python SDK, offering real-time
messaging and presence functionality. It implements the native (synchronous) version of
the PubNub client, building upon the core functionality defined in PubNubCore.

Key Components:
    - PubNub: Main class for interacting with PubNub services
    - NativeSubscriptionManager: Handles channel subscriptions and message processing
    - NativeReconnectionManager: Manages network reconnection strategies
    - NativePublishSequenceManager: Manages message sequence numbers for publishing
    - SubscribeListener: Helper class for handling subscription events
    - NonSubscribeListener: Helper class for handling non-subscription operations

Features:
    - Real-time messaging with publish/subscribe
    - Presence detection and heartbeat
    - Channel and Channel Group support
    - Message queueing and worker thread management
    - Automatic reconnection handling
    - Custom request handler support
    - Telemetry tracking

Usage Example:
    ```python
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub

    config = PNConfiguration()
    config.publish_key = 'your_pub_key'
    config.subscribe_key = 'your_sub_key'
    config.uuid = 'client-123'

    pubnub = PubNub(config)

    # Publish messages
    pubnub.publish().channel("my_channel").message("Hello!").sync()
    ```

Threading Notes:
    - The SDK uses multiple threads for different operations
    - SubscribeMessageWorker runs in a daemon thread
    - Heartbeat and reconnection timers run in separate threads
    - Thread-safe implementations for sequence management and message queuing

Error Handling:
    - Automatic retry mechanisms for failed operations
    - Configurable reconnection policies
    - Status callbacks for error conditions
    - Exception propagation through status objects

Note:
    This implementation is designed for synchronous operations. For asynchronous
    operations, consider using the PubNubAsyncio implementation of the SDK.
"""

import copy
import importlib
import logging
import threading
import os

from typing import Type
from threading import Event
from queue import Queue, Empty
from pubnub import utils
from pubnub.request_handlers.base import BaseRequestHandler
from pubnub.request_handlers.httpx import HttpxRequestHandler
from pubnub.callbacks import SubscribeCallback, ReconnectionCallback
from pubnub.endpoints.presence.heartbeat import Heartbeat
from pubnub.endpoints.presence.leave import Leave
from pubnub.endpoints.pubsub.subscribe import Subscribe
from pubnub.enums import PNStatusCategory, PNHeartbeatNotificationOptions, PNOperationType, PNReconnectionPolicy
from pubnub.managers import SubscriptionManager, PublishSequenceManager, ReconnectionManager, TelemetryManager
from pubnub.models.consumer.common import PNStatus
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_core import PubNubCore
from pubnub.structures import PlatformOptions
from pubnub.workers import SubscribeMessageWorker

logger = logging.getLogger("pubnub")


class PubNub(PubNubCore):
    """Main PubNub client class for synchronous operations.

    This class provides the primary interface for interacting with the PubNub network.
    It implements synchronous (blocking) operations and manages the lifecycle of subscriptions,
    message processing, and network connectivity.

    Attributes:
        config (PNConfiguration): Configuration instance containing SDK settings
    """

    def __init__(self, config: PNConfiguration, *, custom_request_handler: Type[BaseRequestHandler] = None):
        """Initialize a new PubNub instance.

        Args:
            config (PNConfiguration): Configuration instance containing settings
            custom_request_handler (Type[BaseRequestHandler], optional): Custom request handler class.
                Can also be set via set_request_handler method.

        Raises:
            Exception: If custom request handler is not a subclass of BaseRequestHandler
            AssertionError: If config is not an instance of PNConfiguration
        """
        assert isinstance(config, PNConfiguration)
        PubNubCore.__init__(self, config)

        if (not custom_request_handler) and (handler := os.getenv('PUBNUB_REQUEST_HANDLER')):
            module_name, class_name = handler.rsplit('.', 1)
            module = importlib.import_module(module_name)
            custom_request_handler = getattr(module, class_name)
            if not issubclass(custom_request_handler, BaseRequestHandler):
                raise Exception("Custom request handler must be subclass of BaseRequestHandler")
            self._request_handler = custom_request_handler(self)

        if custom_request_handler:
            if not issubclass(custom_request_handler, BaseRequestHandler):
                raise Exception("Custom request handler must be subclass of BaseRequestHandler")
            self._request_handler = custom_request_handler(self)
        else:
            self._request_handler = HttpxRequestHandler(self)

        if self.config.enable_subscribe:
            self._subscription_manager = NativeSubscriptionManager(self)

        self._publish_sequence_manager = PublishSequenceManager(PubNubCore.MAX_SEQUENCE)

        self._telemetry_manager = NativeTelemetryManager()

    def sdk_platform(self) -> str:
        """Get the SDK platform identifier.

        Returns:
            str: An empty string for the native SDK implementation
        """
        return ""

    def set_request_handler(self, handler: BaseRequestHandler) -> None:
        """Set a custom request handler for HTTP operations.

        Args:
            handler (BaseRequestHandler): Instance of custom request handler

        Raises:
            AssertionError: If handler is not an instance of BaseRequestHandler
        """
        assert isinstance(handler, BaseRequestHandler)
        self._request_handler = handler

    def get_request_handler(self) -> BaseRequestHandler:
        """Get the current request handler instance.

        Returns:
            BaseRequestHandler: The current request handler instance
        """
        return self._request_handler

    def request_sync(self, endpoint_call_options):
        """Execute a synchronous request to the PubNub network.

        Args:
            endpoint_call_options: Options for the endpoint call

        Returns:
            The response from the PubNub network

        Note:
            This is an internal method used by endpoint classes
        """
        platform_options = PlatformOptions(self.headers, self.config)
        self.merge_in_params(endpoint_call_options)

        if self.config.log_verbosity:
            print(endpoint_call_options)
        return self._request_handler.sync_request(platform_options, endpoint_call_options)

    def request_async(self, endpoint_name, endpoint_call_options, callback, cancellation_event):
        """Execute an asynchronous request to the PubNub network.

        Args:
            endpoint_name: Name of the endpoint being called
            endpoint_call_options: Options for the endpoint call
            callback: Callback function for the response
            cancellation_event: Event to cancel the request

        Returns:
            The async request object

        Note:
            This is an internal method used by endpoint classes
        """
        platform_options = PlatformOptions(self.headers, self.config)
        self.merge_in_params(endpoint_call_options)

        if self.config.log_verbosity:
            print(endpoint_call_options)
            tt = endpoint_call_options.params["tt"] if "tt" in endpoint_call_options.params else 0
            print(f'\033[48;5;236m{endpoint_name=}, {endpoint_call_options.path}, TT={tt}\033[0m\n')

        return self._request_handler.threaded_request(
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
        """Stop all subscriptions and clean up resources.

        Raises:
            Exception: If subscription manager is not enabled
        """
        if self._subscription_manager is not None:
            self._subscription_manager.stop()
        else:
            raise Exception("Subscription manager is not enabled for this instance")

    def request_deferred(self, options_func):
        raise NotImplementedError

    def request_future(self, *args, **kwargs):
        raise NotImplementedError


class NativeReconnectionManager(ReconnectionManager):
    """Manages reconnection attempts for lost network connections.

    This class implements the reconnection policy (linear or exponential backoff)
    and handles the timing of reconnection attempts.
    """

    def __init__(self, pubnub):
        super(NativeReconnectionManager, self).__init__(pubnub)

    def _register_heartbeat_timer(self):
        """Register a new heartbeat timer for reconnection attempts.

        This method implements the reconnection policy and schedules the next
        reconnection attempt based on the current state.
        """
        self.stop_heartbeat_timer()

        if self._retry_limit_reached():
            logger.warning("Reconnection retry limit reached. Disconnecting.")
            disconnect_status = PNStatus()
            disconnect_status.category = PNStatusCategory.PNDisconnectedCategory
            self._pubnub._subscription_manager._listener_manager.announce_status(disconnect_status)
            return

        self._recalculate_interval()

        self._timer = threading.Timer(self._timer_interval, self._call_time)
        self._timer.daemon = True
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
        """Start the reconnection polling process.

        This method begins the process of attempting to reconnect to the PubNub
        network based on the configured reconnection policy.
        """
        if self._pubnub.config.reconnect_policy == PNReconnectionPolicy.NONE:
            logger.warning("reconnection policy is disabled, please handle reconnection manually.")
            disconnect_status = PNStatus()
            disconnect_status.category = PNStatusCategory.PNDisconnectedCategory
            self._pubnub._subscription_manager._listener_manager.announce_status(disconnect_status)
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
    """Manages channel subscriptions and message processing.

    This class handles the subscription lifecycle, message queuing,
    and delivery of messages to listeners.

    Attributes:
        _message_queue (Queue): Queue for incoming messages
        _consumer_event (Event): Event for controlling the consumer thread
        _subscribe_call: Current subscription API call
        _heartbeat_periodic_callback: Callback for periodic heartbeats
    """

    def __init__(self, pubnub_instance):
        """Initialize the subscription manager.

        Args:
            pubnub_instance: The PubNub instance this manager belongs to
        """
        subscription_manager = self

        self._message_queue = Queue()
        self._consumer_event = threading.Event()
        self._subscribe_call = None
        self._heartbeat_periodic_callback = None
        self._reconnection_manager = NativeReconnectionManager(pubnub_instance)
        self.events = []

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
            if status.is_error():
                if heartbeat_verbosity in (PNHeartbeatNotificationOptions.ALL, PNHeartbeatNotificationOptions.FAILURES):
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
        """Reconnect all current subscriptions.

        Restarts the subscribe loop and heartbeat timer if enabled.
        """
        self._should_stop = False
        self._start_subscribe_loop()
        if self._pubnub.config.enable_presence_heartbeat is True:
            self._register_heartbeat_timer()

    def disconnect(self):
        """Disconnect from all subscriptions.

        Stops the subscribe loop and heartbeat timer.
        """
        self._should_stop = True
        self._stop_heartbeat_timer()
        self._stop_subscribe_loop()

    def _start_worker(self):
        consumer = NativeSubscribeMessageWorker(
            self._pubnub,
            self._listener_manager,
            self._message_queue,
            self._consumer_event
        )
        self._consumer_thread = threading.Thread(
            target=consumer.run,
            name="SubscribeMessageWorker",
            daemon=True).start()

    def _start_subscribe_loop(self):
        self._stop_subscribe_loop()
        event = threading.Event()
        self.events.append(event)

        combined_channels = self._subscription_state.prepare_channel_list(True)
        combined_groups = self._subscription_state.prepare_channel_group_list(True)

        if len(combined_channels) == 0 and len(combined_groups) == 0:
            return

        def callback(raw_result, status):
            """ SubscribeEndpoint callback"""
            if status.is_error():
                if status and status.category == PNStatusCategory.PNCancelledCategory:
                    return

                if status.category is PNStatusCategory.PNTimeoutCategory and not self._should_stop:
                    self._start_subscribe_loop()
                    return

                logger.error("Exception in subscribe loop: %s" % str(status.error_data.exception))

                if status and status.category == PNStatusCategory.PNAccessDeniedCategory:
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
                .cancellation_event(event) \
                .pn_async(callback)
        except Exception as e:
            logger.error("Subscribe request failed: %s" % e)

    def _stop_subscribe_loop(self):
        sc = self._subscribe_call
        for event in self.events:
            event.set()
            self.events.remove(event)

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
        self._timeout.daemon = True
        self._timeout.start()


class NativeSubscribeMessageWorker(SubscribeMessageWorker):
    def _take_message(self):
        while not self._event.is_set():
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
    """Helper class for handling subscription events.

    This class provides a way to wait for specific events or messages
    in a synchronous manner.

    Attributes:
        connected (bool): Whether currently connected
        connected_event (Event): Event signaling connection
        disconnected_event (Event): Event signaling disconnection
        presence_queue (Queue): Queue for presence events
        message_queue (Queue): Queue for messages
        channel_queue (Queue): Queue for channel events
        uuid_queue (Queue): Queue for UUID events
        membership_queue (Queue): Queue for membership events
    """

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
        """Wait for a connection to be established.

        Raises:
            Exception: If already connected
        """
        if not self.connected_event.is_set():
            self.connected_event.wait()

    def wait_for_disconnect(self):
        """Wait for a disconnection to occur.

        Raises:
            Exception: If already disconnected
        """
        if not self.disconnected_event.is_set():
            self.disconnected_event.wait()

    def wait_for_message_on(self, *channel_names):
        """Wait for a message on specific channels.

        Args:
            *channel_names: Channel names to wait for

        Returns:
            The message envelope when received
        """
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
    """Helper class for handling non-subscription operations.

    This class provides a way to wait for the completion of non-subscription
    operations in a synchronous manner.

    Attributes:
        result: The operation result
        status: The operation status
        done_event (Event): Event signaling operation completion
    """

    def __init__(self):
        self.result = None
        self.status = None
        self.done_event = Event()

    def callback(self, result, status):
        self.result = result
        self.status = status
        self.done_event.set()

    def pn_await(self, timeout=5):
        """Wait for the operation to complete.

        Args:
            timeout (int): Maximum time to wait in seconds

        Returns:
            bool: False if timeout occurred, True otherwise
        """
        return self.done_event.wait(timeout)

    def await_result(self, timeout=5):
        """Wait for and return the operation result.

        Args:
            timeout (int): Maximum time to wait in seconds

        Returns:
            The operation result
        """
        self.pn_await(timeout)
        return self.result

    def await_result_and_reset(self, timeout=5):
        """Wait for the result and reset the listener.

        Args:
            timeout (int): Maximum time to wait in seconds

        Returns:
            Copy of the operation result
        """
        self.pn_await(timeout)
        cp = copy.copy(self.result)
        self.reset()
        return cp

    def reset(self):
        """Reset the listener state."""
        self.result = None
        self.status = None
        self.done_event.clear()


class NativeTelemetryManager(TelemetryManager):
    def store_latency(self, latency, operation_type):
        super(NativeTelemetryManager, self).store_latency(latency, operation_type)
        self.clean_up_telemetry_data()
