import asyncio

from queue import SimpleQueue
from typing import Union
from pubnub.endpoints.pubsub.subscribe import Subscribe
from pubnub.pubnub import PubNub
from pubnub.event_engine.models import effects, events
from pubnub.models.consumer.common import PNStatus
from pubnub.workers import SubscribeMessageWorker


class ManagedEffect:
    pubnub: PubNub = None
    event_engine = None
    effect: Union[effects.PNManageableEffect, effects.PNCancelEffect]

    def set_pn(self, pubnub: PubNub):
        self.pubnub = pubnub

    def __init__(self, pubnub_instance, event_engine_instance,
                 effect: Union[effects.PNManageableEffect, effects.PNCancelEffect]) -> None:
        self.effect = effect
        self.event_engine = event_engine_instance
        self.pubnub = pubnub_instance

    def run(self):
        pass

    def run_async(self):
        pass

    def stop(self):
        pass


class ManageHandshakeEffect(ManagedEffect):
    def run(self):
        channels = self.effect.channels
        groups = self.effect.groups
        if hasattr(self.pubnub, 'event_loop'):
            loop: asyncio.AbstractEventLoop = self.pubnub.event_loop
            if loop.is_running():
                loop.create_task(self.handshake_async(channels, groups))
            else:
                loop.run_until_complete(self.handshake_async(channels, groups))
        else:
            # TODO:  the synchronous way
            pass

    def stop(self):
        pass

    async def handshake_async(self, channels, groups):
        handshake = await Subscribe(self.pubnub).channels(channels).channel_groups(groups).future()
        if not handshake.status.error:
            cursor = handshake.result['t']
            timetoken = cursor['t']
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
            loop: asyncio.AbstractEventLoop = self.pubnub.event_loop
            coro = self.receive_messages_async(channels, groups, timetoken, region)
            if loop.is_running():
                loop.create_task(coro)
            else:
                loop.run_until_complete(coro)
        else:
            # TODO:  the synchronous way
            pass

    def stop(self):
        pass

    async def receive_messages_async(self, channels, groups, timetoken, region):
        response = await Subscribe(self.pubnub).channels(channels).channel_groups(groups).timetoken(timetoken) \
            .region(region).future()

        if not response.status.error:
            cursor = response.result['t']
            timetoken = cursor['t']
            region = cursor['r']
            messages = response.result['m']
            print(response.result)
            recieve_success = events.ReceiveSuccessEvent(timetoken, region=region, messages=messages)
            self.event_engine.trigger(recieve_success)


class ManagedEffectFactory:
    _managed_effects = {
        effects.HandshakeEffect.__name__: ManageHandshakeEffect,
        effects.ReceiveMessagesEffect.__name__: ManagedReceiveMessagesEffect,
    }

    def __init__(self, pubnub_instance, event_engine_instance) -> None:
        self._pubnub = pubnub_instance
        self._event_engine = event_engine_instance

    def create(self, effect: ManagedEffect):
        if effect.__class__.__name__ not in self._managed_effects:
            # TODO replace below with raise unsupported managed effect exception
            return ManagedEffect(self._pubnub, self._event_engine, effect)
        return self._managed_effects[effect.__class__.__name__](self._pubnub, self._event_engine, effect)


class EmitEffect:
    pubnub: PubNub

    def set_pn(self, pubnub: PubNub):
        self.pubnub = pubnub
        self.queue = SimpleQueue
        self.message_worker = SubscribeMessageWorker(self.pubnub, None, None, None)

    def emit(self, effect: effects.PNEmittableEffect):
        if isinstance(effect, effects.EmitMessagesEffect):
            self.emit_message(effect)
        if isinstance(effect, effects.EmitStatusEffect):
            self.emit_status(effect)

    def emit_message(self, effect: effects.EmitMessagesEffect):
        self.pubnub._subscription_manager._listener_manager.announce_message('foo')

    def emit_status(self, effect: effects.EmitStatusEffect):
        pn_status = PNStatus()
        pn_status.category = effect.status
        pn_status.error = False
        self.pubnub._subscription_manager._listener_manager.announce_status(pn_status)
