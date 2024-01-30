import asyncio
import logging
import math

from typing import Optional, Union
from pubnub.endpoints.presence.heartbeat import Heartbeat
from pubnub.endpoints.presence.leave import Leave
from pubnub.endpoints.pubsub.subscribe import Subscribe
from pubnub.enums import PNReconnectionPolicy
from pubnub.exceptions import PubNubException
from pubnub.features import feature_enabled
from pubnub.models.server.subscribe import SubscribeMessage
from pubnub.pubnub import PubNub
from pubnub.event_engine.models import effects, events
from pubnub.models.consumer.common import PNStatus
from pubnub.workers import BaseMessageWorker


class ManagedEffect:
    pubnub: PubNub = None
    event_engine = None
    effect: Union[effects.PNManageableEffect, effects.PNCancelEffect]
    stop_event = None
    logger: logging.Logger
    task: asyncio.Task

    def set_pn(self, pubnub: PubNub):
        self.pubnub = pubnub

    def __init__(self, pubnub_instance, event_engine_instance,
                 effect: Union[effects.PNManageableEffect, effects.PNCancelEffect]) -> None:
        self.effect = effect
        self.event_engine = event_engine_instance
        self.pubnub = pubnub_instance

        self.logger = logging.getLogger("pubnub")

    def run(self):
        pass

    def run_async(self, coro):
        loop: asyncio.AbstractEventLoop = self.pubnub.event_loop
        if loop.is_running():
            self.task = loop.create_task(coro)
        else:
            self.task = loop.run_until_complete(coro)

    def stop(self):
        if self.stop_event:
            self.logger.debug(f'stop_event({id(self.stop_event)}).set() called on {self.__class__.__name__}')
            self.stop_event.set()
        if hasattr(self, 'task') and isinstance(self.task, asyncio.Task) and not self.task.cancelled():
            self.task.cancel()

    def get_new_stop_event(self):
        event = asyncio.Event()
        self.logger.debug(f'creating new stop_event({id(event)}) for {self.__class__.__name__}')
        return event


class ManageHandshakeEffect(ManagedEffect):
    def run(self):
        channels = self.effect.channels
        groups = self.effect.groups
        tt = self.effect.timetoken or 0
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.handshake_async(channels=channels,
                                                groups=groups,
                                                timetoken=tt,
                                                stop_event=self.stop_event))

    async def handshake_async(self, channels, groups, stop_event, timetoken: int = 0):
        request = Subscribe(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)
        if feature_enabled('PN_MAINTAIN_PRESENCE_STATE'):
            # request.set_state(self._context.states)  # stub for state handling
            pass

        request.timetoken(0)
        response = await request.future()

        if isinstance(response, PubNubException):
            self.logger.warning(f'Handshake failed: {str(response)}')
            handshake_failure = events.HandshakeFailureEvent(str(response), 1, timetoken=timetoken)
            self.event_engine.trigger(handshake_failure)
        elif response.status.error:
            self.logger.warning(f'Handshake failed: {response.status.error_data.__dict__}')
            handshake_failure = events.HandshakeFailureEvent(response.status.error_data, 1, timetoken=timetoken)
            self.event_engine.trigger(handshake_failure)
        else:
            cursor = response.result['t']
            timetoken = timetoken if timetoken > 0 else cursor['t']
            region = cursor['r']
            handshake_success = events.HandshakeSuccessEvent(timetoken, region)
            self.event_engine.trigger(handshake_success)


class ManagedReceiveMessagesEffect(ManagedEffect):
    effect: effects.ReceiveMessagesEffect

    def run(self):
        channels = self.effect.channels
        groups = self.effect.groups
        timetoken = self.effect.timetoken
        region = self.effect.region

        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.receive_messages_async(channels, groups, timetoken, region))

    async def receive_messages_async(self, channels, groups, timetoken, region):
        request = Subscribe(self.pubnub)
        if channels:
            request.channels(channels)
        if groups:
            request.channel_groups(groups)
        if timetoken:
            request.timetoken(timetoken)
        if region:
            request.region(region)

        request.cancellation_event(self.stop_event)
        response = await request.future()

        if response.status is None and response.result is None:
            self.logger.warning('Recieve messages failed: Empty response')
            recieve_failure = events.ReceiveFailureEvent('Empty response', 1, timetoken=timetoken)
            self.event_engine.trigger(recieve_failure)
        elif response.status.error:
            self.logger.warning(f'Recieve messages failed: {response.status.error_data.__dict__}')
            recieve_failure = events.ReceiveFailureEvent(response.status.error_data, 1, timetoken=timetoken)
            self.event_engine.trigger(recieve_failure)
        else:
            cursor = response.result['t']
            timetoken = cursor['t']
            region = cursor['r']
            messages = response.result['m']
            recieve_success = events.ReceiveSuccessEvent(timetoken, region=region, messages=messages)
            self.event_engine.trigger(recieve_success)
        self.stop_event.set()


class ManagedReconnectEffect(ManagedEffect):
    effect: effects.ReconnectEffect
    reconnection_policy: PNReconnectionPolicy

    def __init__(self, pubnub_instance, event_engine_instance,
                 effect: Union[effects.PNManageableEffect, effects.PNCancelEffect]) -> None:
        super().__init__(pubnub_instance, event_engine_instance, effect)
        self.reconnection_policy = pubnub_instance.config.reconnect_policy
        self.max_retry_attempts = pubnub_instance.config.maximum_reconnection_retries
        self.interval = pubnub_instance.config.RECONNECTION_INTERVAL
        self.min_backoff = pubnub_instance.config.RECONNECTION_MIN_EXPONENTIAL_BACKOFF
        self.max_backoff = pubnub_instance.config.RECONNECTION_MAX_EXPONENTIAL_BACKOFF

    def give_up(self, reason: PubNubException, attempt: int, timetoken: int = 0):
        self.logger.error(f"GiveUp called on Unspecific event. Reason: {reason}, Attempt: {attempt} TT:{timetoken}")
        raise PubNubException('Unspecified Effect')

    def failure(self, reason: PubNubException, attempt: int, timetoken: int = 0):
        self.logger.error(f"Failure called on Unspecific event. Reason: {reason}, Attempt: {attempt} TT:{timetoken}")
        raise PubNubException('Unspecified Effect')

    def success(self, timetoken: str, region: Optional[int] = None, **kwargs):
        self.logger.error(f"Success called on Unspecific event. TT:{timetoken}, Reg: {region}, KWARGS: {kwargs.keys()}")
        raise PubNubException('Unspecified Effect')

    def calculate_reconnection_delay(self, attempts):
        if self.reconnection_policy is PNReconnectionPolicy.LINEAR:
            delay = self.interval

        elif self.reconnection_policy is PNReconnectionPolicy.EXPONENTIAL:
            delay = int(math.pow(2, attempts - 5 * math.floor((attempts - 1) / 5)) - 1)
        return delay

    def run(self):
        if self.reconnection_policy is PNReconnectionPolicy.NONE or self.effect.attempts > self.max_retry_attempts:
            self.give_up(reason=self.effect.reason, attempt=self.effect.attempts)
        else:
            attempts = self.effect.attempts
            delay = self.calculate_reconnection_delay(attempts)
            self.logger.warning(f'will reconnect in {delay}s')
            if hasattr(self.pubnub, 'event_loop'):
                self.run_async(self.delayed_reconnect_async(delay, attempts))

    async def delayed_reconnect_async(self, delay, attempt):
        self.stop_event = self.get_new_stop_event()
        await asyncio.sleep(delay)

        request = Subscribe(self.pubnub).timetoken(self.get_timetoken()).cancellation_event(self.stop_event)

        if self.effect.channels:
            request.channels(self.effect.channels)
        if self.effect.groups:
            request.channel_groups(self.effect.groups)

        if self.effect.region:
            request.region(self.effect.region)

        if feature_enabled('PN_MAINTAIN_PRESENCE_STATE'):
            # subscribe.set_state(self._context.states)  # stub for state handling
            pass

        response = await request.future()

        if isinstance(response, PubNubException):
            self.logger.warning(f'Reconnect failed: {str(response)}')
            self.failure(str(response), attempt, self.get_timetoken())

        elif response.status.error:
            self.logger.warning(f'Reconnect failed: {response.status.error_data.__dict__}')
            self.failure(response.status.error_data, attempt, self.get_timetoken())
        else:
            cursor = response.result['t']
            timetoken = int(self.effect.timetoken) if self.effect.timetoken else cursor['t']
            region = cursor['r']
            messages = response.result['m']
            self.success(timetoken=timetoken, region=region, messages=messages)

    def stop(self):
        self.logger.debug(f'stop called on {self.__class__.__name__}')
        if self.stop_event:
            self.logger.debug(f'stop_event({id(self.stop_event)}).set() called on {self.__class__.__name__}')
            self.stop_event.set()
            if self.task:
                try:
                    self.task.cancel()
                except asyncio.exceptions.CancelledError:
                    pass


class ManagedHandshakeReconnectEffect(ManagedReconnectEffect):
    def give_up(self, reason: PubNubException, attempt: int, timetoken: int = 0):
        self.event_engine.trigger(
            events.HandshakeReconnectGiveupEvent(reason, attempt, timetoken)
        )

    def failure(self, reason: PubNubException, attempt: int, timetoken: int = 0):
        self.event_engine.trigger(
            events.HandshakeReconnectFailureEvent(reason, attempt, timetoken)
        )

    def success(self, timetoken: str, region: Optional[int] = None, **kwargs):
        self.event_engine.trigger(
            events.HandshakeReconnectSuccessEvent(timetoken, region)
        )

    def get_timetoken(self):
        return 0


class ManagedReceiveReconnectEffect(ManagedReconnectEffect):
    def give_up(self, reason: PubNubException, attempt: int, timetoken: int = 0):
        self.event_engine.trigger(
            events.ReceiveReconnectGiveupEvent(reason, attempt, timetoken)
        )

    def failure(self, reason: PubNubException, attempt: int, timetoken: int = 0):
        self.event_engine.trigger(
            events.ReceiveReconnectFailureEvent(reason, attempt, timetoken)
        )

    def success(self, timetoken: str, region: Optional[int] = None, messages=None):

        self.event_engine.trigger(
            events.ReceiveReconnectSuccessEvent(timetoken=timetoken, region=region, messages=messages)
        )

    def get_timetoken(self):
        return int(self.effect.timetoken)


class ManagedHeartbeatEffect(ManagedEffect):
    def run(self):
        channels = self.effect.channels
        groups = self.effect.groups
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.heartbeat(channels=channels, groups=groups, stop_event=self.stop_event))

    async def heartbeat(self, channels, groups, stop_event):
        request = Heartbeat(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)

        if feature_enabled('PN_MAINTAIN_PRESENCE_STATE'):
            # subscribe.set_state(self._context.states)  # stub for state handling
            pass

        response = await request.future()

        if isinstance(response, PubNubException):
            self.logger.warning(f'Heartbeat failed: {str(response)}')
            self.event_engine.trigger(events.HeartbeatFailureEvent(channels=channels, groups=groups,
                                                                   reason=response.status.error_data, attempt=1))
        elif response.status.error:
            self.logger.warning(f'Heartbeat failed: {response.status.error_data.__dict__}')
            self.event_engine.trigger(events.HeartbeatFailureEvent(channels=channels, groups=groups,
                                                                   reason=response.status.error_data, attempt=1))
        else:
            self.event_engine.trigger(events.HeartbeatSuccessEvent(channels=channels, groups=groups))


class ManagedHeartbeatWaitEffect(ManagedEffect):
    def __init__(self, pubnub_instance, event_engine_instance, effect: effects.HeartbeatWaitEffect) -> None:
        super().__init__(pubnub_instance, event_engine_instance, effect)
        self.heartbeat_interval = pubnub_instance.config.heartbeat_interval

    def run(self):
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.heartbeat_wait(self.heartbeat_interval, stop_event=self.stop_event))

    async def heartbeat_wait(self, wait_time: int, stop_event):
        try:
            await asyncio.sleep(wait_time)
            self.event_engine.trigger(events.HeartbeatTimesUpEvent())
        except asyncio.CancelledError:
            pass


class ManagedHeartbeatLeaveEffect(ManagedEffect):
    def run(self):
        channels = self.effect.channels
        groups = self.effect.groups
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.leave(channels=channels, groups=groups, stop_event=self.stop_event))

    async def leave(self, channels, groups, stop_event):
        leave_request = Leave(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)
        leave = await leave_request.future()

        if leave.status.error:
            self.logger.warning(f'Heartbeat failed: {leave.status.error_data.__dict__}')


class ManagedHeartbeatDelayedEffect(ManagedEffect):
    def __init__(self, pubnub_instance, event_engine_instance,
                 effect: Union[effects.PNManageableEffect, effects.PNCancelEffect]) -> None:
        super().__init__(pubnub_instance, event_engine_instance, effect)
        self.reconnection_policy = pubnub_instance.config.reconnect_policy
        self.max_retry_attempts = pubnub_instance.config.maximum_reconnection_retries
        self.interval = pubnub_instance.config.RECONNECTION_INTERVAL
        self.min_backoff = pubnub_instance.config.RECONNECTION_MIN_EXPONENTIAL_BACKOFF
        self.max_backoff = pubnub_instance.config.RECONNECTION_MAX_EXPONENTIAL_BACKOFF

    def calculate_reconnection_delay(self, attempts):
        if self.reconnection_policy is PNReconnectionPolicy.LINEAR:
            delay = self.interval

        elif self.reconnection_policy is PNReconnectionPolicy.EXPONENTIAL:
            delay = int(math.pow(2, attempts - 5 * math.floor((attempts - 1) / 5)) - 1)
        return delay

    def run(self):
        channels = self.effect.channels
        groups = self.effect.groups
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.heartbeat(channels=channels, groups=groups, attempt=1, stop_event=self.stop_event))

    async def heartbeat(self, channels, groups, attempt, stop_event):
        request = Heartbeat(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)
        delay = self.calculate_reconnection_delay(attempt)
        await asyncio.sleep(delay)

        response = await request.future()
        if isinstance(response, PubNubException):
            self.logger.warning(f'Heartbeat failed: {str(response)}')
            self.event_engine.trigger(events.HeartbeatFailureEvent(channels=channels, groups=groups,
                                                                   reason=response.status.error_data,
                                                                   attempt=attempt + 1))
        elif response.status.error:
            self.logger.warning(f'Heartbeat failed: {response.status.error_data.__dict__}')
            self.event_engine.trigger(events.HeartbeatFailureEvent(channels=channels, groups=groups,
                                                                   reason=response.status.error_data,
                                                                   attempt=attempt + 1))
        else:
            self.event_engine.trigger(events.HeartbeatSuccessEvent(channels=channels, groups=groups))


class ManagedEffectFactory:
    _managed_effects = {
        effects.HandshakeEffect.__name__: ManageHandshakeEffect,
        effects.ReceiveMessagesEffect.__name__: ManagedReceiveMessagesEffect,
        effects.HandshakeReconnectEffect.__name__: ManagedHandshakeReconnectEffect,
        effects.ReceiveReconnectEffect.__name__: ManagedReceiveReconnectEffect,
        effects.HeartbeatEffect.__name__: ManagedHeartbeatEffect,
        effects.HeartbeatWaitEffect.__name__: ManagedHeartbeatWaitEffect,
        effects.HeartbeatDelayedHeartbeatEffect.__name__: ManagedHeartbeatDelayedEffect,
        effects.HeartbeatLeaveEffect.__name__: ManagedHeartbeatLeaveEffect,
    }

    def __init__(self, pubnub_instance, event_engine_instance) -> None:
        self._pubnub = pubnub_instance
        self._event_engine = event_engine_instance

    def create(self, effect: ManagedEffect):
        if effect.__class__.__name__ not in self._managed_effects:
            raise PubNubException(errormsg=f"Unhandled managed effect: {effect.__class__.__name__}")
        return self._managed_effects[effect.__class__.__name__](self._pubnub, self._event_engine, effect)


class EmitEffect:
    pubnub: PubNub
    message_worker: BaseMessageWorker

    def set_pn(self, pubnub: PubNub):
        self.pubnub = pubnub
        self.message_worker = BaseMessageWorker(pubnub)

    def emit(self, effect: effects.PNEmittableEffect):
        if isinstance(effect, effects.EmitMessagesEffect):
            self.emit_message(effect)
        if isinstance(effect, effects.EmitStatusEffect):
            self.emit_status(effect)

    def emit_message(self, effect: effects.EmitMessagesEffect):
        self.message_worker._listener_manager = self.pubnub._subscription_manager._listener_manager
        for message in effect.messages:
            subscribe_message = SubscribeMessage().from_json(message)
            self.message_worker._process_incoming_payload(subscribe_message)

    def emit_status(self, effect: effects.EmitStatusEffect):
        pn_status = PNStatus()
        pn_status.category = effect.status
        pn_status.error = False
        self.pubnub._subscription_manager._listener_manager.announce_status(pn_status)
