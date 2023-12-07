import asyncio
import logging
import math

from typing import Optional, Union
from pubnub.endpoints.pubsub.subscribe import Subscribe
from pubnub.enums import PNReconnectionPolicy
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pn_error_data import PNErrorData
from pubnub.models.consumer.pubsub import PNMessageResult
from pubnub.models.server.subscribe import SubscribeMessage
from pubnub.pubnub import PubNub
from pubnub.event_engine.models import effects, events
from pubnub.models.consumer.common import PNStatus


class ManagedEffect:
    pubnub: PubNub = None
    event_engine = None
    effect: Union[effects.PNManageableEffect, effects.PNCancelEffect]
    stop_event = None
    logger: logging.Logger

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

    def run_async(self):
        pass

    def stop(self):
        if self.stop_event:
            self.logger.debug(f'stop_event({id(self.stop_event)}).set() called on {self.__class__.__name__}')
            self.stop_event.set()

    def get_new_stop_event(self):
        event = asyncio.Event()
        self.logger.debug(f'creating new stop_event({id(event)}) for {self.__class__.__name__}')
        return event


class ManageHandshakeEffect(ManagedEffect):
    def run(self):
        channels = self.effect.channels
        groups = self.effect.groups
        timetoken = self.effect.timetoken or 0
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()

            loop: asyncio.AbstractEventLoop = self.pubnub.event_loop
            if loop.is_running():
                loop.create_task(self.handshake_async(channels=channels, groups=groups, timetoken=timetoken,
                                                      stop_event=self.stop_event))
            else:
                loop.run_until_complete(self.handshake_async(channels=channels, groups=groups, timetoken=timetoken,
                                                             stop_event=self.stop_event))
        else:
            # TODO:  the synchronous way
            pass

    async def handshake_async(self, channels, groups, stop_event, timetoken: int = 0):
        request = Subscribe(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)
        request.timetoken(0)
        handshake = await request.future()

        if handshake.status.error:
            self.logger.warning(f'Handshake failed: {handshake.status.error_data.__dict__}')
            handshake_failure = events.HandshakeFailureEvent(handshake.status.error_data, 1, timetoken=timetoken)
            self.event_engine.trigger(handshake_failure)
        else:
            cursor = handshake.result['t']
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
            loop: asyncio.AbstractEventLoop = self.pubnub.event_loop
            if loop.is_running():
                loop.create_task(self.receive_messages_async(channels, groups, timetoken, region))
            else:
                loop.run_until_complete(self.receive_messages_async(channels, groups, timetoken, region))
        else:
            # TODO:  the synchronous way
            pass

    async def receive_messages_async(self, channels, groups, timetoken, region):
        subscribe = Subscribe(self.pubnub)
        if channels:
            subscribe.channels(channels)
        if groups:
            subscribe.channel_groups(groups)
        if timetoken:
            subscribe.timetoken(timetoken)
        if region:
            subscribe.region(region)

        subscribe.cancellation_event(self.stop_event)
        response = await subscribe.future()

        if response.status is None and response.result is None:

            error = PubNubException("Empty response")
            response.status = PNStatus()
            response.status.error = True
            response.status.error_data = PNErrorData(str(error), error)

        if response.status.error:
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
                loop: asyncio.AbstractEventLoop = self.pubnub.event_loop
                if loop.is_running():
                    self.delayed_reconnect_coro = loop.create_task(self.delayed_reconnect_async(delay, attempts))
                else:
                    self.delayed_reconnect_coro = loop.run_until_complete(self.delayed_reconnect_async(delay, attempts))
            else:
                # TODO:  the synchronous way
                pass

    async def delayed_reconnect_async(self, delay, attempt):
        self.stop_event = self.get_new_stop_event()
        await asyncio.sleep(delay)

        request = Subscribe(self.pubnub) \
            .channels(self.effect.channels) \
            .channel_groups(self.effect.groups) \
            .timetoken(self.get_timetoken()) \
            .cancellation_event(self.stop_event)

        if self.effect.region:
            request.region(self.effect.region)

        reconnect = await request.future()

        if reconnect.status.error:
            self.logger.warning(f'Reconnect failed: {reconnect.status.error_data.__dict__}')
            self.failure(reconnect.status.error_data, attempt, self.get_timetoken())
        else:
            cursor = reconnect.result['t']
            timetoken = int(self.effect.timetoken) if self.effect.timetoken else cursor['t']
            region = cursor['r']
            messages = reconnect.result['m']
            self.success(timetoken=timetoken, region=region, messages=messages)

    def stop(self):
        self.logger.debug(f'stop called on {self.__class__.__name__}')
        if self.stop_event:
            self.logger.debug(f'stop_event({id(self.stop_event)}).set() called on {self.__class__.__name__}')
            self.stop_event.set()
            if self.delayed_reconnect_coro:
                try:
                    self.delayed_reconnect_coro.cancel()
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


class ManagedEffectFactory:
    _managed_effects = {
        effects.HandshakeEffect.__name__: ManageHandshakeEffect,
        effects.ReceiveMessagesEffect.__name__: ManagedReceiveMessagesEffect,
        effects.HandshakeReconnectEffect.__name__: ManagedHandshakeReconnectEffect,
        effects.ReceiveReconnectEffect.__name__: ManagedReceiveReconnectEffect,
    }

    def __init__(self, pubnub_instance, event_engine_instance) -> None:
        self._pubnub = pubnub_instance
        self._event_engine = event_engine_instance

    def create(self, effect: ManagedEffect):
        if effect.__class__.__name__ not in self._managed_effects:
            raise PubNubException(errormsg="Unhandled manage effect")
        return self._managed_effects[effect.__class__.__name__](self._pubnub, self._event_engine, effect)


class EmitEffect:
    pubnub: PubNub

    def set_pn(self, pubnub: PubNub):
        self.pubnub = pubnub

    def emit(self, effect: effects.PNEmittableEffect):
        if isinstance(effect, effects.EmitMessagesEffect):
            self.emit_message(effect)
        if isinstance(effect, effects.EmitStatusEffect):
            self.emit_status(effect)

    def emit_message(self, effect: effects.EmitMessagesEffect):
        for message in effect.messages:
            subscribe_message = SubscribeMessage().from_json(message)
            pn_message_result = PNMessageResult(
                message=subscribe_message.payload,
                subscription=subscribe_message.subscription_match,
                channel=subscribe_message.channel,
                timetoken=int(message['p']['t']),
                user_metadata=subscribe_message.publish_metadata,
                publisher=subscribe_message.issuing_client_id
            )
            self.pubnub._subscription_manager._listener_manager.announce_message(pn_message_result)

    def emit_status(self, effect: effects.EmitStatusEffect):
        pn_status = PNStatus()
        pn_status.category = effect.status
        pn_status.error = False
        self.pubnub._subscription_manager._listener_manager.announce_status(pn_status)
