import events
import effects

from effects import PNEffect
from typing import Union


class PNContext:
    channels: list
    groups: list
    tt: int
    handshake_count: int


class PNState:
    _context: PNContext

    def __init__(self, context: PNContext) -> None:
        self._context = context
        self._transitions = {}

    def on(self, event: events.PNEvent, context: PNContext) -> PNEffect:
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
    effect = []

    def __init__(self,
                 state: PNState,
                 context: Union[None, PNContext] = None,
                 effect: Union[None, list[any]] = None
                 ) -> None:
        self.context = context
        self.state = state
        self.effect = effect


class UnsubscribedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
        }

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        context.channels = event.channels
        context.groups = event.groups
        context.tt = 0
        return PNTransition(state=HandshakingState, context=context)

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        context.channels = event.channels
        context.groups = event.groups
        context.tt = event.timetoken
        context.region = event.region
        return PNTransition(state=ReceivingState, context=context)


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
        super().on_enter(context)
        return effects.HandshakeEffect(context.channels, context.groups)

    def on_exit(self):
        super().on_exit()
        return effects.CancelHandshakeEffect()

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context = context
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.tt = 0

        if event.channels[0] == 'fail':
            next_state = HandshakeReconnectingState \
                if context.handshake_count < HandshakingState.MAX_HANDSHAKE_RETRY_COUNT \
                else HandshakeFailedState
        else:
            next_state = ReceivingState

        return PNTransition(
            state=next_state,
            context=self._context
        )

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        self._context = context
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.tt = 0

        if event.channels[0] == 'fail':
            next_state = HandshakeReconnectingState \
                if context.handshake_count < HandshakingState.MAX_HANDSHAKE_RETRY_COUNT \
                else HandshakeFailedState
        else:
            next_state = ReceivingState

        return PNTransition(
            state=next_state,
            context=self._context
        )

    def reconnecting(self, event: events.HandshakeFailureEvent, context: PNContext) -> PNTransition:
        self._context = context.handshake_count + 1

        if event.channels[0] == 'fail':
            next_state = HandshakeReconnectingState \
                if self._context.handshake_count < HandshakingState.MAX_HANDSHAKE_RETRY_COUNT \
                else HandshakeFailedState
        else:
            next_state = ReceivingState

        return PNTransition(
            state=next_state,
            context=self._context
        )

    def disconnect(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context = {*context, *self._context}
        return PNTransition(
            state=HandshakeStoppedState,
            context=context
        )

    def handshaking_success(self, event: events.HandshakeSuccessEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )


class HandshakeReconnectingState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.DisconnectEvent.__name__: self.disconnect,
            events.HandshakeReconnectGiveupEvent.__name__: self.give_up,
            events.HandshakeReconnectSuccessEvent.__name__: self.success,
            events.SubscriptionRestoredEvent.__name__: self.restored,
            events.HandshakeReconnectFailureEvent.__name__: self.handshake_reconnect,
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,

        }

    def on_enter(self, context: Union[None, PNContext]):
        super().on_enter(context)
        return effects.HandshakeEffect(context.channels, context.groups)

    def on_exit(self):
        super().on_exit()

    def disconnect(self, event: events.DisconnectEvent, context: PNContext) -> PNTransition:
        self._context = {**self._context, **context}

        return PNTransition(
            state=HandshakeStoppedState,
            context=self.context,
            effect=effects.CancelHandshakeEffect()
        )

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        self._context.channels = event.channels
        self._context.groups = event.groups
        self._context.tt = 0

        if event.channels[0] == 'fail':
            next_state = HandshakeReconnectingState \
                if self._context.handshake_count < HandshakingState.MAX_HANDSHAKE_RETRY_COUNT \
                else HandshakeFailedState
        else:
            next_state = ReceivingState

        return PNTransition(
            state=next_state
        )

    def handshake_reconnect(self, event: events.HandshakeReconnectFailureEvent, context: PNContext) -> PNTransition:
        self._context = context.handshake_count + 1

        if event.channels[0] == 'fail':
            next_state = HandshakeReconnectingState \
                if self._context.handshake_count < HandshakingState.MAX_HANDSHAKE_RETRY_COUNT \
                else HandshakeFailedState
        else:
            next_state = ReceivingState

        return PNTransition(
            state=next_state,
            context=self._context
        )

    def give_up(self, event: events.HandshakeReconnectGiveupEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=HandshakeFailedState,
            context=self._context
        )

    def restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )

    def success(self, event: events.HandshakeReconnectSuccessEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )


class HandshakeFailedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.HandshakeReconnectRetryEvent.__name__: self.reconnect_retry,
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
            events.ReconnectEvent.__name__: self.reconnect,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
        }

    def reconnect_retry(self, event: events.HandshakeReconnectRetryEvent, context: PNContext) -> PNTransition:
        return PNTransition(state=HandshakeReconnectingState)

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        return PNTransition(state=HandshakingState)

    def reconnect(self, event: events.ReconnectEvent, context: PNContext) -> PNTransition:
        return PNTransition(state=HandshakingState)

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )


class HandshakeStoppedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.ReconnectEvent.__name__: self.reconnect
        }

    def reconnect(self, event: events.ReconnectEvent, context: PNContext) -> PNTransition:
        return PNTransition(state=HandshakeReconnectingState)


class ReceivingState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
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
        return effects.ReceiveEventsEffect(context.channels, context.groups)

    def on_exit(self):
        super().on_exit()
        return effects.CancelReceiveEventsEffect()

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        return PNTransition(state=self.__class__, context=self._context)

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        return PNTransition(state=self.__class__, context=self._context)

    def receiving_success(self, event: events.ReceiveSuccessEvent, context: PNContext) -> PNTransition:
        return PNTransition(state=self.__class__, context=self._context)

    def receiving_failure(self, event: events.ReceiveFailureEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=ReceiveReconnectingStagte
        )

    def disconnect(self, event: events.DisconnectEvent, context: PNContext) -> PNTransition:
        return PNTransition(state=ReceiveStoppedState)


class ReceiveReconnectingStagte(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {

        }


class ReceiveFailedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.ReceiveReconnectRetryEvent.__name__: self.reconnect_retry,
            events.SubscriptionChangedEvent.__name__: self.subscription_changed,
            events.SubscriptionRestoredEvent.__name__: self.subscription_restored,
            events.ReconnectEvent.__name__: self.reconnect,
        }

    def reconnect_retry(self, event: events.HandshakeReconnectRetryEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )

    def subscription_changed(self, event: events.SubscriptionChangedEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )

    def reconnect(self, event: events.ReconnectEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )

    def subscription_restored(self, event: events.SubscriptionRestoredEvent, context: PNContext) -> PNTransition:
        return PNTransition(
            state=ReceivingState,
            context=self._context
        )


class ReceiveStoppedState(PNState):
    def __init__(self, context: PNContext) -> None:
        super().__init__(context)
        self._transitions = {
            events.ReconnectEvent.__name__: self.reconnect
        }

    def reconnect(self, event: events.ReconnectEvent, context: PNContext) -> PNTransition:
        return PNTransition(state=ReceiveReconnectingStagte)
