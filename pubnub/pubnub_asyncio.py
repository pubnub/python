"""PubNub Python SDK Asyncio Implementation.

This module provides the asynchronous implementation of the PubNub Python SDK using
asyncio. It enables non-blocking operations for real-time communication features
and is designed for use in asyncio-based applications.

Key Components:
    - PubNubAsyncio: Main class for asynchronous PubNub operations
    - AsyncioSubscriptionManager: Async implementation of subscription handling
    - EventEngineSubscriptionManager: Event-driven subscription management
    - AsyncioReconnectionManager: Async network reconnection handling
    - AsyncioPublishSequenceManager: Async message sequence management

Features:
    - Asynchronous publish/subscribe messaging
    - Non-blocking network operations
    - Event-driven architecture
    - Customizable request handling
    - Automatic reconnection with backoff strategies
    - Concurrent message processing

Usage Example:
    ```python
    import asyncio
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio

    async def main():
        config = PNConfiguration()
        config.publish_key = 'your_pub_key'
        config.subscribe_key = 'your_sub_key'
        config.uuid = 'client-123'

        pubnub = PubNubAsyncio(config)

        # Subscribe to channels
        await pubnub.subscribe().channels("my_channel").execute()

        # Publish messages
        await pubnub.publish().channel("my_channel").message("Hello!").future()

        # Cleanup
        await pubnub.stop()

    asyncio.run(main())
    ```

Note:
    This implementation is designed for asynchronous operations using Python's
    asyncio framework. For synchronous operations, use the standard PubNub class.
"""

import importlib
import logging
import asyncio
import math

from asyncio import Event, Queue, Semaphore
import os
from httpx import AsyncHTTPTransport
from pubnub.event_engine.containers import PresenceStateContainer
from pubnub.event_engine.models import events, states

from pubnub.models.consumer.common import PNStatus
from pubnub.dtos import SubscribeOperation, UnsubscribeOperation
from pubnub.event_engine.statemachine import StateMachine
from pubnub.endpoints.presence.heartbeat import Heartbeat
from pubnub.endpoints.presence.leave import Leave
from pubnub.endpoints.pubsub.subscribe import Subscribe
from pubnub.pubnub_core import PubNubCore
from pubnub.request_handlers.base import BaseRequestHandler
from pubnub.request_handlers.async_httpx import AsyncHttpxRequestHandler
from pubnub.workers import SubscribeMessageWorker
from pubnub.managers import SubscriptionManager, PublishSequenceManager, ReconnectionManager, TelemetryManager
from pubnub import utils
from pubnub.enums import PNStatusCategory, PNHeartbeatNotificationOptions, PNOperationType, PNReconnectionPolicy
from pubnub.callbacks import SubscribeCallback, ReconnectionCallback
from pubnub.errors import PNERR_REQUEST_CANCELLED, PNERR_CLIENT_TIMEOUT
from pubnub.exceptions import PubNubAsyncioException, PubNubException

# flake8: noqa
from pubnub.models.envelopes import AsyncioEnvelope

logger = logging.getLogger("pubnub")


class PubNubAsyncHTTPTransport(AsyncHTTPTransport):
    """Custom HTTP transport for asynchronous PubNub operations.

    This class extends AsyncHTTPTransport to provide PubNub-specific
    transport functionality with proper connection state tracking.

    Attributes:
        is_closed (bool): Whether the transport is closed
    """

    is_closed: bool = False

    def close(self):
        """Close the transport connection."""
        self.is_closed = True
        super().aclose()


class PubNubAsyncio(PubNubCore):
    """PubNub Python SDK for asyncio framework.

    This class provides the main interface for asynchronous interactions with
    the PubNub network. It implements all core PubNub functionality in a
    non-blocking manner.

    Attributes:
        event_loop (AbstractEventLoop): The asyncio event loop to use
    """

    def __init__(self, config, custom_event_loop=None, subscription_manager=None, *, custom_request_handler=None):
        """Initialize a new PubNubAsyncio instance.

        Args:
            config: PubNub configuration instance
            custom_event_loop (AbstractEventLoop, optional): Custom event loop to use
            subscription_manager (Type, optional): Custom subscription manager class
            custom_request_handler (Type[BaseRequestHandler], optional): Custom request
                handler class. Can also be set via PUBNUB_ASYNC_REQUEST_HANDLER
                environment variable.

        Raises:
            Exception: If custom request handler is not a subclass of BaseRequestHandler
        """
        super(PubNubAsyncio, self).__init__(config)
        self.event_loop = custom_event_loop or asyncio.get_event_loop()
        self._session = None

        if (not custom_request_handler) and (handler := os.getenv('PUBNUB_ASYNC_REQUEST_HANDLER')):
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
            self._request_handler = AsyncHttpxRequestHandler(self)

        if not subscription_manager:
            subscription_manager = EventEngineSubscriptionManager

        if self.config.enable_subscribe:
            self._subscription_manager = subscription_manager(self)

        self._publish_sequence_manager = AsyncioPublishSequenceManager(self.event_loop, PubNubCore.MAX_SEQUENCE)
        self._telemetry_manager = AsyncioTelemetryManager()

    @property
    def _connector(self):
        return self._request_handler._connector

    async def close_pending_tasks(self, tasks):
        """Close any pending tasks and wait for completion.

        Args:
            tasks: List of tasks to close
        """
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)

    async def create_session(self):
        """Create a new HTTP session."""
        await self._request_handler.create_session()

    async def close_session(self):
        """Close the current HTTP session."""
        await self._request_handler.close_session()

    async def set_connector(self, connector):
        """Set a custom connector for HTTP operations.

        Args:
            connector: The connector to use
        """
        await self._request_handler.set_connector(connector)

    async def stop(self):
        """Stop all operations and clean up resources."""
        if self._subscription_manager:
            self._subscription_manager.stop()
        await self.close_session()

    def sdk_platform(self):
        """Get the SDK platform identifier.

        Returns:
            str: "-Asyncio" to identify this as the asyncio implementation
        """
        return "-Asyncio"

    def request_sync(self, *args):
        raise NotImplementedError

    def request_deferred(self, *args):
        raise NotImplementedError

    async def request_result(self, options_func, cancellation_event):
        """Execute a request and return its result.

        Args:
            options_func: Function that returns request options
            cancellation_event: Event to cancel the request

        Returns:
            The result of the request
        """
        envelope = await self._request_handler.async_request(options_func, cancellation_event)
        return envelope.result

    async def request_future(self, options_func, cancellation_event):
        """Execute a request and return a future.

        This method handles various error conditions and wraps them in
        appropriate exception types.

        Args:
            options_func: Function that returns request options
            cancellation_event: Event to cancel the request

        Returns:
            PubNubAsyncioException: On error
            AsyncioEnvelope: On success
        """
        try:
            res = await self._request_handler.async_request(options_func, cancellation_event)
            return res
        except PubNubException as e:
            return PubNubAsyncioException(
                result=None,
                status=e.status
            )
        except asyncio.TimeoutError:
            return PubNubAsyncioException(
                result=None,
                status=options_func().create_status(
                    PNStatusCategory.PNTimeoutCategory,
                    None,
                    None,
                    exception=PubNubException(
                        pn_error=PNERR_CLIENT_TIMEOUT
                    )
                )
            )
        except asyncio.CancelledError:
            return PubNubAsyncioException(
                result=None,
                status=options_func().create_status(
                    PNStatusCategory.PNCancelledCategory,
                    None,
                    None,
                    exception=PubNubException(
                        pn_error=PNERR_REQUEST_CANCELLED
                    )
                )
            )
        except Exception as e:
            return PubNubAsyncioException(
                result=None,
                status=options_func().create_status(
                    PNStatusCategory.PNUnknownCategory,
                    None,
                    None,
                    e
                )
            )


class AsyncioReconnectionManager(ReconnectionManager):
    """Manages reconnection attempts for lost network connections.

    This class implements the reconnection policy (linear or exponential backoff)
    using asyncio's event loop for timing.

    Attributes:
        _task: The current reconnection task
    """

    def __init__(self, pubnub):
        self._task = None
        super(AsyncioReconnectionManager, self).__init__(pubnub)

    async def _register_heartbeat_timer(self):
        """Register a new heartbeat timer for reconnection attempts.

        This method implements the reconnection policy and schedules the next
        reconnection attempt based on the current state.
        """
        while True:
            self._recalculate_interval()
            await asyncio.sleep(self._timer_interval)
            logger.debug("reconnect loop at: %s" % utils.datetime_now())

            try:
                await self._pubnub.time().future()
                self._connection_errors = 1
                self._callback.on_reconnect()
                break
            except Exception:
                if self._pubnub.config.reconnect_policy == PNReconnectionPolicy.EXPONENTIAL:
                    logger.debug("reconnect interval increment at: %s" % utils.datetime_now())
                    self._connection_errors += 1

    def start_polling(self):
        """Start the reconnection polling process."""
        if self._pubnub.config.reconnect_policy == PNReconnectionPolicy.NONE:
            logger.warning("reconnection policy is disabled, please handle reconnection manually.")
            return

        self._task = asyncio.ensure_future(self._register_heartbeat_timer())

    def stop_polling(self):
        """Stop the reconnection polling process."""
        if self._task is not None and not self._task.cancelled():
            self._task.cancel()


class AsyncioPublishSequenceManager(PublishSequenceManager):
    def __init__(self, ioloop, provided_max_sequence):
        super(AsyncioPublishSequenceManager, self).__init__(provided_max_sequence)
        self._lock = asyncio.Lock()
        self._event_loop = ioloop

    async def get_next_sequence(self):
        async with self._lock:
            if self.max_sequence == self.next_sequence:
                self.next_sequence = 1
            else:
                self.next_sequence += 1

            return self.next_sequence


class AsyncioSubscriptionManager(SubscriptionManager):
    """Manages channel subscriptions and message processing.

    This class handles the subscription lifecycle, message queuing,
    and delivery of messages to listeners using asyncio primitives.

    Attributes:
        _message_queue (Queue): Queue for incoming messages
        _subscription_lock (Semaphore): Lock for subscription operations
        _subscribe_loop_task: Current subscription loop task
        _heartbeat_periodic_callback: Callback for periodic heartbeats
    """

    def __init__(self, pubnub_instance):
        subscription_manager = self

        self._message_worker = None
        self._message_queue = Queue()
        self._subscription_lock = Semaphore(1)
        self._subscribe_loop_task = None
        self._heartbeat_periodic_callback = None
        self._reconnection_manager = AsyncioReconnectionManager(pubnub_instance)

        super(AsyncioSubscriptionManager, self).__init__(pubnub_instance)
        self._start_worker()

        class AsyncioReconnectionCallback(ReconnectionCallback):
            def on_reconnect(self):
                subscription_manager.reconnect()

                pn_status = PNStatus()
                pn_status.category = PNStatusCategory.PNReconnectedCategory
                pn_status.error = False

                subscription_manager._subscription_status_announced = True
                subscription_manager._listener_manager.announce_status(pn_status)

        self._reconnection_listener = AsyncioReconnectionCallback()
        self._reconnection_manager.set_reconnection_listener(self._reconnection_listener)

    def _set_consumer_event(self):
        if not self._message_worker.cancelled():
            self._message_worker.cancel()

    def _message_queue_put(self, message):
        self._message_queue.put_nowait(message)

    def _start_worker(self):
        consumer = AsyncioSubscribeMessageWorker(
            self._pubnub,
            self._listener_manager,
            self._message_queue,
            None
        )
        self._message_worker = asyncio.ensure_future(
            consumer.run(),
            loop=self._pubnub.event_loop
        )

    def reconnect(self):
        """Reconnect all current subscriptions.

        Restarts the subscribe loop and heartbeat timer if enabled.
        """
        self._should_stop = False
        self._subscribe_loop_task = asyncio.ensure_future(self._start_subscribe_loop())
        self._register_heartbeat_timer()

    def disconnect(self):
        """Disconnect from all subscriptions.

        Stops the subscribe loop and heartbeat timer.
        """
        self._should_stop = True
        self._stop_heartbeat_timer()
        self._stop_subscribe_loop()

    def stop(self):
        super(AsyncioSubscriptionManager, self).stop()
        self._reconnection_manager.stop_polling()
        if self._subscribe_loop_task and not self._subscribe_loop_task.cancelled():
            self._subscribe_loop_task.cancel()

    async def _start_subscribe_loop(self):
        """Start the subscription loop.

        This method handles the main subscription process, including
        channel management and error handling.
        """
        self._stop_subscribe_loop()
        await self._subscription_lock.acquire()

        try:
            combined_channels = self._subscription_state.prepare_channel_list(True)
            combined_groups = self._subscription_state.prepare_channel_group_list(True)

            if len(combined_channels) == 0 and len(combined_groups) == 0:
                self._subscription_lock.release()
                return

            self._subscribe_request_task = asyncio.ensure_future(
                Subscribe(self._pubnub)
                .channels(combined_channels)
                .channel_groups(combined_groups)
                .timetoken(self._timetoken)
                .region(self._region)
                .filter_expression(self._pubnub.config.filter_expression)
                .future()
            )

            e = await self._subscribe_request_task

            if self._subscribe_request_task.cancelled():
                return

            if e.is_error():
                await self._handle_subscription_error(e)
            else:
                self._handle_endpoint_call(e.result, e.status)
                self._subscribe_loop_task = asyncio.ensure_future(self._start_subscribe_loop())

        finally:
            self._subscription_lock.release()

    def _stop_subscribe_loop(self):
        if self._subscribe_request_task is not None and not self._subscribe_request_task.cancelled():
            self._subscribe_request_task.cancel()

    def _stop_heartbeat_timer(self):
        if self._heartbeat_periodic_callback is not None:
            self._heartbeat_periodic_callback.stop()

    def _register_heartbeat_timer(self):
        super(AsyncioSubscriptionManager, self)._register_heartbeat_timer()

        self._heartbeat_periodic_callback = AsyncioPeriodicCallback(
            self._perform_heartbeat_loop,
            self._pubnub.config.heartbeat_interval * 1000,
            self._pubnub.event_loop)
        if not self._should_stop:
            self._heartbeat_periodic_callback.start()

    async def _perform_heartbeat_loop(self):
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
            heartbeat_call = (Heartbeat(self._pubnub)
                              .channels(presence_channels)
                              .channel_groups(presence_groups)
                              .state(state_payload)
                              .cancellation_event(cancellation_event)
                              .future())

            envelope = await heartbeat_call

            heartbeat_verbosity = self._pubnub.config.heartbeat_notification_options
            if envelope.status.is_error():
                if heartbeat_verbosity in (PNHeartbeatNotificationOptions.ALL, PNHeartbeatNotificationOptions.FAILURES):
                    self._listener_manager.announce_status(envelope.status)
            else:
                if heartbeat_verbosity == PNHeartbeatNotificationOptions.ALL:
                    self._listener_manager.announce_status(envelope.status)

        except PubNubAsyncioException:
            pass
            # TODO: check correctness
            # if e.status is not None and e.status.category == PNStatusCategory.PNTimeoutCategory:
            #     self._start_subscribe_loop()
            # else:
            #     self._listener_manager.announce_status(e.status)
        finally:
            cancellation_event.set()

    def _send_leave(self, unsubscribe_operation):
        asyncio.ensure_future(self._send_leave_helper(unsubscribe_operation))

    async def _send_leave_helper(self, unsubscribe_operation):
        envelope = await Leave(self._pubnub) \
            .channels(unsubscribe_operation.channels) \
            .channel_groups(unsubscribe_operation.channel_groups).future()

        self._listener_manager.announce_status(envelope.status)

    async def _handle_subscription_error(self, error):
        """Handle errors that occur during subscription.

        Args:
            error: The error that occurred
        """
        if error.status and error.status.category == PNStatusCategory.PNCancelledCategory:
            return

        if error.status and error.status.category == PNStatusCategory.PNTimeoutCategory:
            asyncio.ensure_future(self._start_subscribe_loop())
            return

        logger.error("Exception in subscribe loop: %s" % str(error))

        if error.status and error.status.category == PNStatusCategory.PNAccessDeniedCategory:
            error.status.operation = PNOperationType.PNUnsubscribeOperation

        self._listener_manager.announce_status(error.status)
        self._reconnection_manager.start_polling()
        self.disconnect()


class EventEngineSubscriptionManager(SubscriptionManager):
    event_engine: StateMachine
    loop: asyncio.AbstractEventLoop

    def __init__(self, pubnub_instance):
        self.state_container = PresenceStateContainer()
        self.event_engine = StateMachine(states.UnsubscribedState,
                                         name="subscribe")
        self.presence_engine = StateMachine(states.HeartbeatInactiveState,
                                            name="presence")
        self.event_engine.get_dispatcher().set_pn(pubnub_instance)
        self.presence_engine.get_dispatcher().set_pn(pubnub_instance)
        self.loop = asyncio.new_event_loop()
        self._heartbeat_periodic_callback = None
        pubnub_instance.state_container = self.state_container
        super().__init__(pubnub_instance)

    def stop(self):
        self.event_engine.stop()
        self.presence_engine.stop()

    def adapt_subscribe_builder(self, subscribe_operation: SubscribeOperation):
        if not isinstance(subscribe_operation, SubscribeOperation):
            raise PubNubException('Invalid Subscribe Operation')

        if subscribe_operation.timetoken:
            subscription_event = events.SubscriptionRestoredEvent(
                channels=subscribe_operation.channels_with_pressence,
                groups=subscribe_operation.groups_with_pressence,
                timetoken=subscribe_operation.timetoken,
                with_presence=subscribe_operation.presence_enabled
            )
        else:
            subscription_event = events.SubscriptionChangedEvent(
                channels=subscribe_operation.channels_with_pressence,
                groups=subscribe_operation.groups_with_pressence,
                with_presence=subscribe_operation.presence_enabled
            )
        self.event_engine.trigger(subscription_event)
        if self._pubnub.config.enable_presence_heartbeat and self._pubnub.config._heartbeat_interval > 0:
            self.presence_engine.trigger(events.HeartbeatJoinedEvent(
                channels=subscribe_operation.channels_without_presence,
                groups=subscribe_operation.channel_groups_without_presence
            ))

    def adapt_unsubscribe_builder(self, unsubscribe_operation):
        if not isinstance(unsubscribe_operation, UnsubscribeOperation):
            raise PubNubException('Invalid Unsubscribe Operation')

        channels = unsubscribe_operation.get_subscribed_channels(self.event_engine.get_context().channels)

        groups = unsubscribe_operation.get_subscribed_channel_groups(self.event_engine.get_context().groups)

        if channels or groups:
            self.event_engine.trigger(events.SubscriptionChangedEvent(channels=channels, groups=groups))
        else:
            self.event_engine.trigger(events.UnsubscribeAllEvent())

        if self._pubnub.config.enable_presence_heartbeat and self._pubnub.config._heartbeat_interval > 0:
            self.presence_engine.trigger(event=events.HeartbeatLeftEvent(
                channels=unsubscribe_operation.channels_without_presence,
                groups=unsubscribe_operation.channel_groups_without_presence,
                suppress_leave=self._pubnub.config.suppress_leave_events
            ))

    def adapt_state_builder(self, state_operation):
        self.state_container.register_state(state_operation.state,
                                            state_operation.channels)
        return super().adapt_state_builder(state_operation)

    def unsubscribe_all(self):
        self.adapt_unsubscribe_builder(UnsubscribeOperation(
            channels=self.get_subscribed_channels(),
            channel_groups=self.get_subscribed_channel_groups()))

    def get_custom_params(self):
        return {'ee': 1}

    def get_subscribed_channels(self):
        return self.event_engine.get_context().channels

    def get_subscribed_channel_groups(self):
        return self.event_engine.get_context().groups

    def _stop_heartbeat_timer(self):
        self.presence_engine.trigger(events.HeartbeatLeftAllEvent(
            suppress_leave=self._pubnub.config.suppress_leave_events))
        self.presence_engine.stop()


class AsyncioSubscribeMessageWorker(SubscribeMessageWorker):
    async def run(self):
        await self._take_message()

    async def _take_message(self):
        while True:
            try:
                msg = await self._queue.get()
                if msg is not None:
                    self._process_incoming_payload(msg)
                self._queue.task_done()
            except asyncio.CancelledError:
                logger.debug("Message Worker cancelled")
                break
            except Exception as e:
                logger.error("take message interrupted: %s" % str(e))
                raise


class AsyncioPeriodicCallback(object):
    def __init__(self, callback, callback_time, event_loop):
        self._callback = callback
        self._callback_time = callback_time
        self._event_loop = event_loop
        self._next_timeout = None
        self._running = False
        self._timeout = None

    def start(self):
        self._running = True
        self._next_timeout = self._event_loop.time()
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
            asyncio.ensure_future(self._callback())
        except Exception:
            raise
        finally:
            self._schedule_next()

    def _schedule_next(self):
        current_time = self._event_loop.time()

        if self._next_timeout <= current_time:
            callback_time_sec = self._callback_time / 1000.0
            self._next_timeout += (math.floor(
                (current_time - self._next_timeout) / callback_time_sec) + 1) * callback_time_sec

        self._timeout = self._event_loop.call_at(self._next_timeout, self._run)


class SubscribeListener(SubscribeCallback):
    """Helper class for handling subscription events.

    This class provides a way to wait for specific events or messages
    in an asynchronous manner.

    Attributes:
        connected (bool): Whether currently connected
        connected_event (Event): Event signaling connection
        disconnected_event (Event): Event signaling disconnection
        presence_queue (Queue): Queue for presence events
        message_queue (Queue): Queue for messages
        error_queue (Queue): Queue for errors
    """

    def __init__(self):
        self.connected = False
        self.connected_event = Event()
        self.disconnected_event = Event()
        self.presence_queue = Queue()
        self.message_queue = Queue()
        self.error_queue = Queue()

    def status(self, pubnub, status):
        """Handle status updates from the PubNub instance.

        Args:
            pubnub: The PubNub instance
            status: The status update
        """
        super().status(pubnub, status)
        if utils.is_subscribed_event(status) and not self.connected_event.is_set():
            self.connected_event.set()
        elif utils.is_unsubscribed_event(status) and not self.disconnected_event.is_set():
            self.disconnected_event.set()
        elif status.is_error():
            self.error_queue.put_nowait(status.error_data.exception)

    def message(self, pubnub, message):
        """Handle incoming messages from the PubNub instance.

        Args:
            pubnub: The PubNub instance
            message: The incoming message
        """
        self.message_queue.put_nowait(message)

    def presence(self, pubnub, presence):
        """Handle presence updates from the PubNub instance.

        Args:
            pubnub: The PubNub instance
            presence: The presence update
        """
        self.presence_queue.put_nowait(presence)

    async def _wait_for(self, coro):
        """Wait for a coroutine to complete.

        Args:
            coro: The coroutine to wait for

        Returns:
            The result of the coroutine

        Raises:
            Exception: If an error occurs while waiting
        """
        scc_task = asyncio.ensure_future(coro)
        err_task = asyncio.ensure_future(self.error_queue.get())

        await asyncio.wait([
            scc_task,
            err_task
        ], return_when=asyncio.FIRST_COMPLETED)

        if err_task.done() and not scc_task.done():
            if not scc_task.cancelled():
                scc_task.cancel()
            raise err_task.result()
        else:
            if not err_task.cancelled():
                err_task.cancel()
            return scc_task.result()

    async def wait_for_connect(self):
        """Wait for a connection to be established."""
        if not self.connected_event.is_set():
            await self._wait_for(self.connected_event.wait())

    async def wait_for_disconnect(self):
        """Wait for a disconnection to occur."""
        if not self.disconnected_event.is_set():
            await self._wait_for(self.disconnected_event.wait())

    async def wait_for_message_on(self, *channel_names):
        """Wait for a message on specific channels.

        Args:
            *channel_names: Channel names to wait for

        Returns:
            The message envelope when received

        Raises:
            Exception: If an error occurs while waiting
        """
        channel_names = list(channel_names)
        while True:
            try:
                env = await self._wait_for(self.message_queue.get())
                if env.channel in channel_names:
                    return env
                else:
                    continue
            finally:
                self.message_queue.task_done()

    async def wait_for_presence_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            try:
                env = await self._wait_for(self.presence_queue.get())
                if env.channel in channel_names:
                    return env
                else:
                    continue
            finally:
                self.presence_queue.task_done()


class AsyncioTelemetryManager(TelemetryManager):
    def __init__(self):
        TelemetryManager.__init__(self)
        self.loop = asyncio.get_event_loop()
        self._schedule_next_cleanup()

    def _schedule_next_cleanup(self):
        self._timer = self.loop.call_later(
            self.CLEAN_UP_INTERVAL * self.CLEAN_UP_INTERVAL_MULTIPLIER / 1000,
            self._clean_up_schedule_next
        )

    def _clean_up_schedule_next(self):
        self.clean_up_telemetry_data()
        self._schedule_next_cleanup()

    def _stop_clean_up_timer(self):
        self._timer.cancel()
