import asyncio
import logging

from queue import SimpleQueue
from typing import Union
from pubnub.endpoints.pubsub.subscribe import Subscribe
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
        logging.debug(f'stop called on {self.__class__.__name__}')
        if self.stop_event:
            logging.debug(f'stop_event({id(self.stop_event)}).set() called on {self.__class__.__name__}')
            self.stop_event.set()

    def get_new_stop_event(self):
        event = asyncio.Event()
        logging.debug(f'creating new stop_event({id(event)}) for {self.__class__.__name__}')
        return event


class ManageHandshakeEffect(ManagedEffect):
    def run(self):
        channels = self.effect.channels
        groups = self.effect.groups
        if hasattr(self.pubnub, 'event_loop'):
            self.stop_event = self.get_new_stop_event()

            loop: asyncio.AbstractEventLoop = self.pubnub.event_loop
            if loop.is_running():
                loop.create_task(self.handshake_async(channels, groups, self.stop_event))
            else:
                loop.run_until_complete(self.handshake_async(channels, groups, self.stop_event))
        else:
            # TODO:  the synchronous way
            pass

    async def handshake_async(self, channels, groups, stop_event):
        request = Subscribe(self.pubnub).channels(channels).channel_groups(groups).cancellation_event(stop_event)
        handshake = await request.future()
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

        if response and response.result:
            if not response.status.error:
                cursor = response.result['t']
                timetoken = cursor['t']
                region = cursor['r']
                messages = response.result['m']
                recieve_success = events.ReceiveSuccessEvent(timetoken, region=region, messages=messages)
                self.event_engine.trigger(recieve_success)
        self.stop_event.set()


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
