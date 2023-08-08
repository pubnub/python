import logging
import json
import asyncio
import aiohttp
import math
import time
import urllib

from asyncio import Event, Queue, Semaphore
from yarl import URL
from pubnub.event_engine.models import events, states

from pubnub.models.consumer.common import PNStatus
from pubnub.dtos import SubscribeOperation, UnsubscribeOperation
from pubnub.event_engine.statemachine import StateMachine
from pubnub.endpoints.presence.heartbeat import Heartbeat
from pubnub.endpoints.presence.leave import Leave
from pubnub.endpoints.pubsub.subscribe import Subscribe
from pubnub.pubnub_core import PubNubCore
from pubnub.workers import SubscribeMessageWorker
from pubnub.managers import SubscriptionManager, PublishSequenceManager, ReconnectionManager, TelemetryManager
from pubnub import utils
from pubnub.structures import ResponseInfo, RequestOptions
from pubnub.enums import PNStatusCategory, PNHeartbeatNotificationOptions, PNOperationType, PNReconnectionPolicy
from pubnub.callbacks import SubscribeCallback, ReconnectionCallback
from pubnub.errors import (
    PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_JSON_DECODING_FAILED,
    PNERR_REQUEST_CANCELLED, PNERR_CLIENT_TIMEOUT
)
from .exceptions import PubNubException

logger = logging.getLogger("pubnub")


class PubNubAsyncio(PubNubCore):
    """
    PubNub Python SDK for asyncio framework
    """

    def __init__(self, config, custom_event_loop=None, subscription_manager=None):
        super(PubNubAsyncio, self).__init__(config)
        self.event_loop = custom_event_loop or asyncio.get_event_loop()

        self._connector = None
        self._session = None

        self._connector = aiohttp.TCPConnector(verify_ssl=True, loop=self.event_loop)

        if not subscription_manager:
            subscription_manager = AsyncioSubscriptionManager

        if self.config.enable_subscribe:
            self._subscription_manager = subscription_manager(self)

        self._publish_sequence_manager = AsyncioPublishSequenceManager(self.event_loop, PubNubCore.MAX_SEQUENCE)

        self._telemetry_manager = AsyncioTelemetryManager()

    def __del__(self):
        pass
        if self.event_loop.is_running():
            self.event_loop.create_task(self.close_session())

    async def close_pending_tasks(self, tasks):
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)

    async def create_session(self):
        self._session = aiohttp.ClientSession(
            loop=self.event_loop,
            timeout=aiohttp.ClientTimeout(connect=self.config.connect_timeout),
            connector=self._connector
        )

    async def close_session(self):
        if self._session is not None:
            await self._session.close()

    async def set_connector(self, cn):
        await self._session.close()

        self._connector = cn

        self._session = aiohttp.ClientSession(
            loop=self.event_loop,
            timeout=aiohttp.ClientTimeout(connect=self.config.connect_timeout),
            connector=self._connector
        )

    async def stop(self):
        await self.close_session()
        if self._subscription_manager:
            self._subscription_manager.stop()

    def sdk_platform(self):
        return "-Asyncio"

    def request_sync(self, *args):
        raise NotImplementedError

    def request_deferred(self, *args):
        raise NotImplementedError

    async def request_result(self, options_func, cancellation_event):
        envelope = await self._request_helper(options_func, cancellation_event)
        return envelope.result

    async def request_future(self, options_func, cancellation_event):
        try:
            res = await self._request_helper(options_func, cancellation_event)
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

    async def _request_helper(self, options_func, cancellation_event):
        """
        Query string should be provided as a manually serialized and encoded string.

        :param options_func:
        :param cancellation_event:
        :return:
        """
        if cancellation_event is not None:
            assert isinstance(cancellation_event, Event)

        options = options_func()
        assert isinstance(options, RequestOptions)

        create_response = options.create_response
        create_status = options.create_status
        create_exception = options.create_exception

        params_to_merge_in = {}

        if options.operation_type == PNOperationType.PNPublishOperation:
            params_to_merge_in['seqn'] = await self._publish_sequence_manager.get_next_sequence()

        options.merge_params_in(params_to_merge_in)

        if options.use_base_path:
            url = utils.build_url(self.config.scheme(), self.base_origin, options.path, options.query_string)
        else:
            url = utils.build_url(scheme="", origin="", path=options.path, params=options.query_string)

        url = URL(url, encoded=True)

        logger.debug("%s %s %s" % (options.method_string, url, options.data))

        if options.request_headers:
            request_headers = {**self.headers, **options.request_headers}
        else:
            request_headers = self.headers

        try:
            if not self._session:
                await self.create_session()
            start_timestamp = time.time()
            response = await asyncio.wait_for(
                self._session.request(
                    options.method_string,
                    url,
                    headers=request_headers,
                    data=options.data if options.data else None,
                    allow_redirects=options.allow_redirects
                ),
                options.request_timeout
            )
        except (asyncio.TimeoutError, asyncio.CancelledError):
            raise
        except Exception as e:
            logger.error("session.request exception: %s" % str(e))
            raise

        if not options.non_json_response:
            body = await response.text()
        else:
            if isinstance(response.content, bytes):
                body = response.content  # TODO: simplify this logic within the v5 release
            else:
                body = await response.read()

        if cancellation_event is not None and cancellation_event.is_set():
            return

        response_info = None
        status_category = PNStatusCategory.PNUnknownCategory

        if response:
            request_url = urllib.parse.urlparse(str(response.url))
            query = urllib.parse.parse_qs(request_url.query)
            uuid = None
            auth_key = None

            if 'uuid' in query and len(query['uuid']) > 0:
                uuid = query['uuid'][0]

            if 'auth_key' in query and len(query['auth_key']) > 0:
                auth_key = query['auth_key'][0]

            response_info = ResponseInfo(
                status_code=response.status,
                tls_enabled='https' == request_url.scheme,
                origin=request_url.hostname,
                uuid=uuid,
                auth_key=auth_key,
                client_request=None,
                client_response=response
            )

        # if body is not None and len(body) > 0 and not options.non_json_response:
        if body is not None and len(body) > 0:
            if options.non_json_response:
                data = body
            else:
                try:
                    data = json.loads(body)
                except ValueError:
                    if response.status == 599 and len(body) > 0:
                        data = body
                    else:
                        raise
                except TypeError:
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except ValueError:
                        raise create_exception(
                            category=status_category,
                            response=response,
                            response_info=response_info,
                            exception=PubNubException(
                                pn_error=PNERR_JSON_DECODING_FAILED,
                                errormsg='json decode error',
                            )
                        )
        else:
            data = "N/A"

        logger.debug(data)

        if response.status not in (200, 307, 204):

            if response.status >= 500:
                err = PNERR_SERVER_ERROR
            else:
                err = PNERR_CLIENT_ERROR

            if response.status == 403:
                status_category = PNStatusCategory.PNAccessDeniedCategory

            if response.status == 400:
                status_category = PNStatusCategory.PNBadRequestCategory

            raise create_exception(
                category=status_category,
                response=data,
                response_info=response_info,
                exception=PubNubException(
                    errormsg=data,
                    pn_error=err,
                    status_code=response.status
                )
            )
        else:
            self._telemetry_manager.store_latency(time.time() - start_timestamp, options.operation_type)

            return AsyncioEnvelope(
                result=create_response(data) if not options.non_json_response else create_response(response, data),
                status=create_status(
                    PNStatusCategory.PNAcknowledgmentCategory,
                    data,
                    response_info,
                    None
                )
            )


class AsyncioReconnectionManager(ReconnectionManager):
    def __init__(self, pubnub):
        self._task = None
        super(AsyncioReconnectionManager, self).__init__(pubnub)

    async def _register_heartbeat_timer(self):
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
        if self._pubnub.config.reconnect_policy == PNReconnectionPolicy.NONE:
            logger.warning("reconnection policy is disabled, please handle reconnection manually.")
            return

        self._task = asyncio.ensure_future(self._register_heartbeat_timer())

    def stop_polling(self):
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
        # TODO: method is synchronized in Java
        self._should_stop = False
        self._subscribe_loop_task = asyncio.ensure_future(self._start_subscribe_loop())
        self._register_heartbeat_timer()

    def disconnect(self):
        # TODO: method is synchronized in Java
        self._should_stop = True
        self._stop_heartbeat_timer()
        self._stop_subscribe_loop()

    def stop(self):
        super(AsyncioSubscriptionManager, self).stop()
        self._reconnection_manager.stop_polling()
        if self._subscribe_loop_task and not self._subscribe_loop_task.cancelled():
            self._subscribe_loop_task.cancel()

    async def _start_subscribe_loop(self):
        self._stop_subscribe_loop()

        await self._subscription_lock.acquire()

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
            self._subscription_lock.release()
            return

        if e.is_error():
            if e.status and e.status.category == PNStatusCategory.PNCancelledCategory:
                self._subscription_lock.release()
                return

            if e.status and e.status.category == PNStatusCategory.PNTimeoutCategory:
                asyncio.ensure_future(self._start_subscribe_loop())
                self._subscription_lock.release()
                return

            logger.error("Exception in subscribe loop: %s" % str(e))

            if e.status and e.status.category == PNStatusCategory.PNAccessDeniedCategory:
                e.status.operation = PNOperationType.PNUnsubscribeOperation

            # TODO: raise error
            self._listener_manager.announce_status(e.status)

            self._reconnection_manager.start_polling()
            self._subscription_lock.release()
            self.disconnect()
            return
        else:
            self._handle_endpoint_call(e.result, e.status)
            self._subscription_lock.release()
            self._subscribe_loop_task = asyncio.ensure_future(self._start_subscribe_loop())

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


class EventEngineSubscriptionManager(SubscriptionManager):
    event_engine: StateMachine
    loop: asyncio.AbstractEventLoop

    def __init__(self, pubnub_instance):
        self.event_engine = StateMachine(states.UnsubscribedState)
        self.event_engine.get_dispatcher().set_pn(pubnub_instance)
        self.loop = asyncio.new_event_loop()

        super().__init__(pubnub_instance)

    def stop(self):
        self.event_engine.stop()

    def adapt_subscribe_builder(self, subscribe_operation: SubscribeOperation):
        if not isinstance(subscribe_operation, SubscribeOperation):
            raise PubNubException('Invalid Subscribe Operation')

        if subscribe_operation.timetoken:
            subscription_event = events.SubscriptionRestoredEvent(
                channels=subscribe_operation.channels,
                groups=subscribe_operation.channel_groups,
                timetoken=subscribe_operation.timetoken
            )
        else:
            subscription_event = events.SubscriptionChangedEvent(
                channels=subscribe_operation.channels,
                groups=subscribe_operation.channel_groups
            )
        self.event_engine.trigger(subscription_event)

    def adapt_unsubscribe_builder(self, unsubscribe_operation):
        if not isinstance(unsubscribe_operation, UnsubscribeOperation):
            raise PubNubException('Invalid Unsubscribe Operation')
        event = events.SubscriptionChangedEvent(None, None)
        self.event_engine.trigger(event)


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


class AsyncioEnvelope(object):
    def __init__(self, result, status):
        self.result = result
        self.status = status

    @staticmethod
    def is_error():
        return False


class PubNubAsyncioException(Exception):
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
        self.message_queue.put_nowait(message)

    def presence(self, pubnub, presence):
        self.presence_queue.put_nowait(presence)

    async def _wait_for(self, coro):
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
        if not self.connected_event.is_set():
            await self._wait_for(self.connected_event.wait())
        else:
            raise Exception("instance is already connected")

    async def wait_for_disconnect(self):
        if not self.disconnected_event.is_set():
            await self._wait_for(self.disconnected_event.wait())
        else:
            raise Exception("instance is already disconnected")

    async def wait_for_message_on(self, *channel_names):
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
        self._timer = AsyncioPeriodicCallback(
            self._start_clean_up_timer,
            self.CLEAN_UP_INTERVAL * self.CLEAN_UP_INTERVAL_MULTIPLIER,
            asyncio.get_event_loop())
        self._timer.start()

    async def _start_clean_up_timer(self):
        self.clean_up_telemetry_data()

    def _stop_clean_up_timer(self):
        self._timer.stop()
