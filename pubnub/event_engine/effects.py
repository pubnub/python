import asyncio
import logging

from typing import Optional, Union
from pubnub.endpoints.presence.heartbeat import Heartbeat
from pubnub.endpoints.presence.leave import Leave
from pubnub.endpoints.pubsub.subscribe import Subscribe
from pubnub.enums import PNReconnectionPolicy
from pubnub.exceptions import PubNubException
from pubnub.features import feature_enabled
from pubnub.models.server.subscribe import SubscribeMessage
from pubnub.pubnub import PubNub
from pubnub.event_engine.models import events, invocations
from pubnub.models.consumer.common import PNStatus
from pubnub.workers import BaseMessageWorker
from pubnub.managers import LinearDelay, ExponentialDelay


class Effect:
    pubnub: PubNub = None
    event_engine = None
    invocation: Union[invocations.PNManageableInvocation, invocations.PNCancelInvocation]
    stop_event = None
    logger: logging.Logger
    task: asyncio.Task

    def set_pn(self, pubnub: PubNub):
        self.pubnub = pubnub

    def __init__(self, pubnub_instance, event_engine_instance,
                 invocation: Union[invocations.PNManageableInvocation, invocations.PNCancelInvocation]) -> None:
        self.invocation = invocation
        self.event_engine = event_engine_instance
        self.pubnub = pubnub_instance

        self.logger = logging.getLogger("pubnub")

    def run(self):
        pass

    def run_async(self, coro):
        loop: asyncio.AbstractEventLoop = self.pubnub.event_loop
        if loop.is_running():
            self.task = loop.create_task(coro, name=self.__class__.__name__)
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


class HandshakeEffect(Effect):
    def run(self):
        channels = self.invocation.channels
        groups = self.invocation.groups
        tt = self.invocation.timetoken or 0
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.handshake_async(channels=channels,
                                                groups=groups,
                                                timetoken=tt,
                                                stop_event=self.stop_event))

    async def handshake_async(self, channels, groups, stop_event, timetoken: int = 0):
        request = Subscribe(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)

        if feature_enabled('PN_MAINTAIN_PRESENCE_STATE') and hasattr(self.pubnub, 'state_container'):
            state_container = self.pubnub.state_container
            request.state(state_container.get_state(channels))

        request.timetoken(0)
        response = await request.future()

        if isinstance(response, Exception):
            self.logger.warning(f'Handshake failed: {str(response)}')
            handshake_failure = events.HandshakeFailureEvent(response, 1, timetoken=timetoken)
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


class ReceiveMessagesEffect(Effect):
    invocation: invocations.ReceiveMessagesInvocation

    def run(self):
        channels = self.invocation.channels
        groups = self.invocation.groups
        timetoken = self.invocation.timetoken
        region = self.invocation.region

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
            if self.stop_event.is_set():
                self.logger.debug(f'Recieve messages cancelled: {response.status.error_data.__dict__}')
                return
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


class ReconnectEffect(Effect):
    invocation: invocations.ReconnectInvocation
    reconnection_policy: PNReconnectionPolicy

    def __init__(self, pubnub_instance, event_engine_instance,
                 invocation: Union[invocations.PNManageableInvocation, invocations.PNCancelInvocation]) -> None:
        super().__init__(pubnub_instance, event_engine_instance, invocation)
        self.reconnection_policy = pubnub_instance.config.reconnect_policy
        self.interval = pubnub_instance.config.reconnection_interval

        if self.reconnection_policy is PNReconnectionPolicy.EXPONENTIAL:
            self.max_retry_attempts = ExponentialDelay.MAX_RETRIES
        elif self.reconnection_policy is PNReconnectionPolicy.LINEAR:
            self.max_retry_attempts = LinearDelay.MAX_RETRIES

        if pubnub_instance.config.maximum_reconnection_retries is not None:
            self.max_retry_attempts = pubnub_instance.config.maximum_reconnection_retries

    def give_up(self, reason: PubNubException, attempt: int, timetoken: int = 0):
        self.logger.error(f"GiveUp called on Unspecific event. Reason: {reason}, Attempt: {attempt} TT:{timetoken}")
        raise PubNubException('Unspecified Invocation')

    def failure(self, reason: PubNubException, attempt: int, timetoken: int = 0):
        self.logger.error(f"Failure called on Unspecific event. Reason: {reason}, Attempt: {attempt} TT:{timetoken}")
        raise PubNubException('Unspecified Invocation')

    def success(self, timetoken: str, region: Optional[int] = None, **kwargs):
        self.logger.error(f"Success called on Unspecific event. TT:{timetoken}, Reg: {region}, KWARGS: {kwargs.keys()}")
        raise PubNubException('Unspecified Invocation')

    def calculate_reconnection_delay(self, attempts):
        if self.reconnection_policy is PNReconnectionPolicy.EXPONENTIAL:
            delay = ExponentialDelay.calculate(attempts)
        elif self.interval is None:
            delay = LinearDelay.calculate(attempts)
        else:
            delay = self.interval

        return delay

    def run(self):
        if self.reconnection_policy is PNReconnectionPolicy.NONE or self.invocation.attempts > self.max_retry_attempts:
            self.give_up(reason=self.invocation.reason, attempt=self.invocation.attempts)
        else:
            attempts = self.invocation.attempts
            delay = self.calculate_reconnection_delay(attempts)
            self.logger.warning(f'Will reconnect in {delay}s')
            if hasattr(self.pubnub, 'event_loop'):
                self.run_async(self.delayed_reconnect_async(delay, attempts))

    async def delayed_reconnect_async(self, delay, attempt):
        self.stop_event = self.get_new_stop_event()
        await asyncio.sleep(delay)

        request = Subscribe(self.pubnub).timetoken(self.get_timetoken()).cancellation_event(self.stop_event)

        if self.invocation.channels:
            request.channels(self.invocation.channels)
        if self.invocation.groups:
            request.channel_groups(self.invocation.groups)

        if self.invocation.region:
            request.region(self.invocation.region)

        if feature_enabled('PN_MAINTAIN_PRESENCE_STATE') and hasattr(self.pubnub, 'state_container'):
            state_container = self.pubnub.state_container
            request.state(state_container.get_state(self.invocation.channels))

        response = await request.future()

        if isinstance(response, PubNubException):
            self.logger.warning(f'Reconnect failed: {str(response)}')
            self.failure(str(response), attempt, self.get_timetoken())

        elif response.status.error:
            self.logger.warning(f'Reconnect failed: {response.status.error_data.__dict__}')
            self.failure(response.status.error_data, attempt, self.get_timetoken())
        elif 't' in response.result:
            cursor = response.result['t']
            timetoken = int(self.invocation.timetoken) if self.invocation.timetoken else cursor['t']
            region = cursor['r']
            messages = response.result['m']
            self.success(timetoken=timetoken, region=region, messages=messages)
        else:
            self.logger.warning(f'Reconnect failed: Invalid response {str(response)}')
            self.failure(str(response), attempt, self.get_timetoken())

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


class HandshakeReconnectEffect(ReconnectEffect):
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


class ReceiveReconnectEffect(ReconnectEffect):
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
        return int(self.invocation.timetoken)


class HeartbeatEffect(Effect):
    def run(self):
        channels = list(filter(lambda ch: not ch.endswith('-pnpres'), self.invocation.channels))
        groups = list(filter(lambda gr: not gr.endswith('-pnpres'), self.invocation.groups))

        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.heartbeat(channels=channels, groups=groups, stop_event=self.stop_event))

    async def heartbeat(self, channels, groups, stop_event):
        request = Heartbeat(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)

        if feature_enabled('PN_MAINTAIN_PRESENCE_STATE') and hasattr(self.pubnub, 'state_container'):
            state_container = self.pubnub.state_container
            request.state(state_container.get_state(self.invocation.channels))

        response = await request.future()

        if isinstance(response, PubNubException):
            self.logger.warning(f'Heartbeat failed: {str(response)}')
            self.event_engine.trigger(events.HeartbeatFailureEvent(channels=channels, groups=groups,
                                                                   reason=response.status.error_data, attempt=1))
        elif response.status and response.status.error:
            self.logger.warning(f'Heartbeat failed: {response.status.error_data.__dict__}')
            self.event_engine.trigger(events.HeartbeatFailureEvent(channels=channels, groups=groups,
                                                                   reason=response.status.error_data, attempt=1))
        else:
            self.event_engine.trigger(events.HeartbeatSuccessEvent(channels=channels, groups=groups))


class HeartbeatWaitEffect(Effect):
    def __init__(self, pubnub_instance, event_engine_instance, invocation: invocations.HeartbeatWaitInvocation) -> None:
        super().__init__(pubnub_instance, event_engine_instance, invocation)
        self.heartbeat_interval = pubnub_instance.config.heartbeat_interval

    def run(self):
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.heartbeat_wait(self.heartbeat_interval, stop_event=self.stop_event))

    async def heartbeat_wait(self, wait_time: int, stop_event):
        try:
            await asyncio.sleep(wait_time)
            if not stop_event.is_set():
                self.event_engine.trigger(events.HeartbeatTimesUpEvent())
        except asyncio.CancelledError:
            pass


class HeartbeatLeaveEffect(Effect):
    def run(self):
        channels = self.invocation.channels
        groups = self.invocation.groups
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.leave(channels=channels, groups=groups, stop_event=self.stop_event))

    async def leave(self, channels, groups, stop_event):
        leave_request = Leave(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)
        leave = await leave_request.future()

        if leave.status.error:
            self.logger.warning(f'Heartbeat failed: {leave.status.error_data.__dict__}')


class HeartbeatDelayedEffect(Effect):
    def __init__(self, pubnub_instance, event_engine_instance,
                 invocation: Union[invocations.PNManageableInvocation, invocations.PNCancelInvocation]) -> None:
        super().__init__(pubnub_instance, event_engine_instance, invocation)
        self.reconnection_policy = pubnub_instance.config.reconnect_policy
        self.max_retry_attempts = pubnub_instance.config.maximum_reconnection_retries
        self.interval = pubnub_instance.config.reconnection_interval

    def calculate_reconnection_delay(self, attempts):
        if self.reconnection_policy is PNReconnectionPolicy.EXPONENTIAL:
            delay = ExponentialDelay.calculate(attempts)
        elif self.interval is None:
            delay = LinearDelay.calculate(attempts)
        else:
            delay = self.interval

        return delay

    def run(self):
        if self.reconnection_policy is PNReconnectionPolicy.NONE or self.invocation.attempts > self.max_retry_attempts:
            self.event_engine.trigger(events.HeartbeatGiveUpEvent(channels=self.invocation.channels,
                                                                  groups=self.invocation.groups,
                                                                  reason=self.invocation.reason,
                                                                  attempt=self.invocation.attempts))

        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()
            self.run_async(self.heartbeat(channels=self.invocation.channels, groups=self.invocation.groups,
                                          attempt=self.invocation.attempts, stop_event=self.stop_event))

    async def heartbeat(self, channels, groups, attempt, stop_event):
        if self.reconnection_policy is PNReconnectionPolicy.NONE or self.invocation.attempts > self.max_retry_attempts:
            self.event_engine.trigger(events.HeartbeatGiveUpEvent(channels=self.invocation.channels,
                                                                  groups=self.invocation.groups,
                                                                  reason=self.invocation.reason,
                                                                  attempt=self.invocation.attempts))

        channels = list(filter(lambda ch: not ch.endswith('-pnpres'), self.invocation.channels))
        groups = list(filter(lambda gr: not gr.endswith('-pnpres'), self.invocation.groups))

        request = Heartbeat(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)
        delay = self.calculate_reconnection_delay(attempt)
        self.logger.warning(f'Will retry to Heartbeat in {delay}s')
        await asyncio.sleep(delay)

        response = await request.future()
        if isinstance(response, PubNubException):
            self.logger.warning(f'Heartbeat failed: {str(response)}')
            self.event_engine.trigger(events.HeartbeatFailureEvent(channels=channels, groups=groups,
                                                                   reason=response.status.error_data,
                                                                   attempt=attempt))
        elif response.status.error:
            self.logger.warning(f'Heartbeat failed: {response.status.error_data.__dict__}')
            self.event_engine.trigger(events.HeartbeatFailureEvent(channels=channels, groups=groups,
                                                                   reason=response.status.error_data,
                                                                   attempt=attempt))
        else:
            self.event_engine.trigger(events.HeartbeatSuccessEvent(channels=channels, groups=groups))


class EffectFactory:
    _managed_invocations = {
        invocations.HandshakeInvocation.__name__: HandshakeEffect,
        invocations.ReceiveMessagesInvocation.__name__: ReceiveMessagesEffect,
        invocations.HandshakeReconnectInvocation.__name__: HandshakeReconnectEffect,
        invocations.ReceiveReconnectInvocation.__name__: ReceiveReconnectEffect,
        invocations.HeartbeatInvocation.__name__: HeartbeatEffect,
        invocations.HeartbeatWaitInvocation.__name__: HeartbeatWaitEffect,
        invocations.HeartbeatDelayedHeartbeatInvocation.__name__: HeartbeatDelayedEffect,
        invocations.HeartbeatLeaveInvocation.__name__: HeartbeatLeaveEffect,
    }

    def __init__(self, pubnub_instance, event_engine_instance) -> None:
        self._pubnub = pubnub_instance
        self._event_engine = event_engine_instance

    def create(self, invocation: invocations.PNInvocation) -> Effect:
        if invocation.__class__.__name__ not in self._managed_invocations:
            raise PubNubException(errormsg=f"Unhandled Invocation: {invocation.__class__.__name__}")
        return self._managed_invocations[invocation.__class__.__name__](self._pubnub, self._event_engine, invocation)


class EmitEffect:
    pubnub: PubNub
    message_worker: BaseMessageWorker

    def set_pn(self, pubnub: PubNub):
        self.pubnub = pubnub
        self.message_worker = BaseMessageWorker(pubnub)

    def emit(self, invocation: invocations.PNEmittableInvocation):
        if isinstance(invocation, list):
            for inv in invocation:
                self.emit(inv)
        if isinstance(invocation, invocations.EmitMessagesInvocation):
            self.emit_message(invocation)
        if isinstance(invocation, invocations.EmitStatusInvocation):
            self.emit_status(invocation)

    def emit_message(self, invocation: invocations.EmitMessagesInvocation):
        self.message_worker._listener_manager = self.pubnub._subscription_manager._listener_manager
        for message in invocation.messages:
            subscribe_message = SubscribeMessage().from_json(message)
            self.message_worker._process_incoming_payload(subscribe_message)

    def emit_status(self, invocation: invocations.EmitStatusInvocation):
        if isinstance(invocation.status, PNStatus):
            self.pubnub._subscription_manager._listener_manager.announce_status(invocation.status)
            return
        pn_status = PNStatus()
        pn_status.category = invocation.status
        pn_status.operation = invocation.operation
        if invocation.context and invocation.context.channels:
            pn_status.affected_channels = invocation.context.channels
        if invocation.context and invocation.context.groups:
            pn_status.affected_groups = invocation.context.groups
        pn_status.error = False
        self.pubnub._subscription_manager._listener_manager.announce_status(pn_status)
