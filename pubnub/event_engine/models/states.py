from pubnub.enums import PNStatusCategory
from pubnub.event_engine.models import effects
from pubnub.event_engine.models.effects import PNEffect
from pubnub.event_engine.models import events
from pubnub.exceptions import PubNubException
from typing import List, Union


class PNContext(dict):
    channels: list
    groups: list
    region: int
    timetoken: str
    attempt: int
    reason: PubNubException

    def update(self, context):
        super().update(context.__dict__)


class PNState:
    _context: PNContext

    def __init__(self, context: PNContext) -> None:
        self._context = context
        self._transitions = dict

    def on(self, event: events.PNEvent, context: PNContext):
        return self._transitions[event.get_name()](event, context)

    def on_enter(self, context: Union[None, PNContext]):
        pass

    def on_exit(self):
        pass

    def get_context(self) -> PNContext:
        return self._context


class PNTransition:
    context: PNContext
    state: PNState
    effect: Union[None, List[PNEffect]]

    def __init__(self,
                 state: PNState,
                 context: Union[None, PNContext] = None,
                 effect: Union[None, List[PNEffect]] = None,
                 ) -> None:
        self.context = context
        self.state = state
        self.effect = effect


class UnsubscribedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._context.attempt = 0

        self._transitions = {
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
        }

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = 0

        return PNTransition(
            state=HandshakingState,
            context=self._context
        )

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=ReceivingState,
            context=self._context
        )


class HandshakingState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.HandshakeFailureEvent.__name__: self.reconnecting,
            events.DisconnectEvent.__name__: self.disconnect,
            events.HandshakeSuccessEvent.__name__: self.handshaking_success,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
        }

    def on_enter(self, context: Union[None, PNContext]):
        self._context.update(context)
        super().on_enter(self._context)
        return effects.HandshakeEffect(self._context.channels, self._context.groups)

    def on_exit(self):
        super().on_exit()
        return effects.CancelHandshakeEffect()

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = 0

        return PNTransition(
            state=HandshakingState,
            context=self._context
        )

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=ReceivingState,
            context=self._context
        )

    def reconnecting(self, event: events.HandshakeFailureEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.attempt = event.attempt
        self._context.reason = event.reason

        return PNTransition(
            state=HandshakeReconnectingState,
            context=self._context
        )

    def disconnect(self, event: events.DisconnectEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.timetoken = 0

        return PNTransition(
            state=HandshakeStoppedState,
            context=self._context
        )

    def handshaking_success(self, event: events.HandshakeSuccessEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=ReceivingState,
            context=self._context,
            effect=effects.EmitStatusEffect(PNStatusCategory.PNConnectedCategory)
        )


class HandshakeReconnectingState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.DisconnectEvent.__name__: self.disconnect,
            events.HandshakeReconnectGiveupEvent.__name__: self.give_up,
            events.HandshakeReconnectSuccessEvent.__name__: self.success,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
            events.HandshakeReconnectFailureEvent.__name__: self.handshake_reconnect,
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
        }

    def on_enter(self, context: Union[None, PNContext]):
        self._context.update(context)
        super().on_enter(self._context)
        return effects.HandshakeReconnectEffect(self._context.channels,
                                                self._context.groups,
                                                attempts=self._context.attempt,
                                                reason=self._context.reason)

    def on_exit(self):
        super().on_exit()
        return effects.CancelHandshakeReconnectEffect()

    def disconnect(self, event: events.DisconnectEvent, context: PNContext) -> PNTransition:
        self._context.update(context)

        return PNTransition(
            state=HandshakeStoppedState,
            context=self._context
        )

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = 0

        return PNTransition(
            state=HandshakeReconnectingState,
            context=self._context
        )

    def handshake_reconnect(self, event: events.HandshakeReconnectFailureEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.attempt = event.attempt + 1
        self._context.reason = event.reason

        return PNTransition(
            state=HandshakeReconnectingState,
            context=self._context
        )

    def give_up(self, event: events.HandshakeReconnectGiveupEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.attempt = event.attempt
        self._context.reason = event.reason

        return PNTransition(
            state=HandshakeFailedState,
            context=self._context
        )

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=ReceivingState,
            context=self._context
        )

    def success(self, event: events.HandshakeReconnectSuccessEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=ReceivingState,
            context=self._context,
            effect=effects.EmitStatusEffect(PNStatusCategory.PNConnectedCategory, )
        )


class HandshakeFailedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
            events.ReconnectEvent.__name__: self.reconnect,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
        }

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = 0

        return PNTransition(
            state=HandshakingState,
            context=self._context
        )

    def reconnect(self, event: events.ReconnectEvent, context: PNContext) -> PNTransition:
        self._context.update(context)

        return PNTransition(
            state=HandshakingState,
            context=self._context
        )

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=ReceivingState,
            context=self._context
        )


class HandshakeStoppedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._context.attempt = 0

        self._transitions = {
            events.ReconnectEvent.__name__: self.reconnect
        }

    def reconnect(self, event: events.ReconnectEvent, context: PNContext) -> PNTransition:
        self._context.update(context)

        return PNTransition(
            state=HandshakeReconnectingState,
            context=self._context
        )


class ReceivingState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._context.attempt = 0

        self._transitions = {
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
            events.ReceiveSuccessEvent.__name__: self.receiving_success,
            events.ReceiveFailureEvent.__name__: self.receiving_failure,
            events.DisconnectEvent.__name__: self.disconnect,
            events.ReconnectEvent.__name__: self.reconnect,
        }

    def on_enter(self, context: Union[None, PNContext]):
        super().on_enter(context)
        return effects.ReceiveMessagesEffect(context.channels, context.groups, timetoken=self._context.timetoken,
                                             region=self._context.region)

    def on_exit(self):
        super().on_exit()
        return effects.CancelReceiveMessagesEffect()

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = 0

        return PNTransition(
            state=self.__class__,
            context=self._context
        )

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=self.__class__,
            context=self._context
        )

    def receiving_success(self, event: events.ReceiveSuccessEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=self.__class__,
            context=self._context,
            effect=[effects.EmitMessagesEffect(messages=event.messages),
                    effects.EmitStatusEffect(PNStatusCategory.PNConnectedCategory)],
        )

    def receiving_failure(self, event: events.ReceiveFailureEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.reason = event.reason

        return PNTransition(
            state=ReceiveReconnectingState,
            context=self._context
        )

    def disconnect(self, event: events.DisconnectEvent, context: PNContext) -> PNTransition:
        self._context.update(context)

        return PNTransition(
            state=ReceiveStoppedState,
            context=self._context,
            effect=effects.EmitStatusEffect(PNStatusCategory.PNDisconnectedCategory)
        )

    def reconnect(self, event: events.ReconnectEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )


class ReceiveReconnectingState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.ReceiveReconnectFailureEvent.__name__: self.reconnect_failure,
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
            events.DisconnectEvent.__name__: self.disconnect,
            events.ReceiveReconnectGiveupEvent.__name__: self.give_up,
            events.ReceiveReconnectSuccessEvent.__name__: self.reconnect_success,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
        }

    def on_enter(self, context: Union[None, PNContext]):
        self._context.update(context)
        super().on_enter(self._context)
        return effects.ReceiveReconnectEffect(self._context.channels, self._context.groups, self._context.timetoken,
                                              self._context.region, self._context.attempt, self._context.reason)

    def on_exit(self):
        super().on_exit()
        return effects.CancelReceiveReconnectEffect()

    def reconnect_failure(self, event: events.ReceiveReconnectFailureEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.attempt = event.attempt + 1
        self._context.reason = event.reason

        return PNTransition(
            state=ReceiveReconnectingState,
            context=self._context
        )

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = 0

        return PNTransition(
            state=ReceiveReconnectingState,
            context=self._context
        )

    def disconnect(self, event: events.DisconnectEvent, context: PNContext) -> PNTransition:
        self._context.update(context)

        return PNTransition(
            state=ReceiveStoppedState,
            context=self._context
        )

    def give_up(self, event: events.ReceiveReconnectGiveupEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.reason = event.reason
        self._context.attempt = event.attempt

        return PNTransition(
            state=ReceiveFailedState,
            context=self._context,
            effect=effects.EmitStatusEffect(PNStatusCategory.PNDisconnectedCategory)
        )

    def reconnect_success(self, event: events.ReceiveReconnectSuccessEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=ReceivingState,
            context=self._context,
            effect=[effects.EmitMessagesEffect(event.messages),
                    effects.EmitStatusEffect(PNStatusCategory.PNConnectedCategory)]
        )

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=ReceiveReconnectingState,
            context=self._context
        )


class ReceiveFailedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.ReceiveReconnectRetryEvent.__name__: self.reconnect_retry,
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
            events.ReconnectEvent.__name__: self.reconnect,
        }

    def reconnect_retry(self, event: events.ReceiveReconnectRetryEvent, context: PNContext) -> PNTransition:
        self._context.update(context)

        return PNTransition(
            state=ReceiveReconnectingState,
            context=self._context
        )

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = 0

        return PNTransition(
            state=ReceivingState,
            context=self._context
        )

    def reconnect(self, event: events.ReconnectEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        self._context.update(context)
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.timetoken = event.timetoken
        self._context.region = event.region

        return PNTransition(
            state=ReceivingState,
            context=self._context
        )


class ReceiveStoppedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._context.attempt = 0

        self._transitions = {
            events.ReconnectEvent.__name__: self.reconnect
        }

    def reconnect(self, event: events.ReconnectEvent, context: PNContext) -> PNTransition:
        self._context.update(context)

        return PNTransition(
            state=ReceiveReconnectingState,
            context=self._context
        )
