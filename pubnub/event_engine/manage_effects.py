import asyncio

from typing import Union
from pubnub.endpoints.pubsub.subscribe import Subscribe
from pubnub.pubnub import PubNub
from pubnub.event_engine.models import effects, events


class ManagedEffect:
    pubnub = None
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
        channels = self.event_engine.get_context().get('channels')
        groups = self.event_engine.get_context().get('groups')
        if hasattr(self.pubnub, 'event_loop'):
            loop: asyncio.AbstractEventLoop = self.pubnub.event_loop
            if loop.is_running():
                loop.create_task(self.handshake_async(channels, groups))
            else:
                loop.run_until_complete(self.handshake_async(channels, groups))
        else:
            # the synchronous way
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


class ManagedEffectFactory:
    _managed_effects = {
        effects.HandshakeEffect.__name__: ManageHandshakeEffect
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

    def set_pn(pubnub: PubNub):
        pubnub = pubnub

    def emit(self, effect: effects.PNEmittableEffect):
        if isinstance(effect, effects.EmitMessagesEffect):
            self.emit_message(effect)
        if isinstance(effect, effects.EmitStatusEffect):
            self.emit_status(effect)

    def emit_message(self, effect: effects.EmitMessagesEffect):
        pass

    def emit_status(self, effect: effects.EmitStatusEffect):
        pass
