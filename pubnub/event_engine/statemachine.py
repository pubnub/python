from pubnub.event_engine import effects, events, states
from pubnub.event_engine.dispatcher import Dispatcher
from typing import List


class StateMachine:
    _current_state: states.PNState
    _context: states.PNContext
    _effect_list: List[effects.PNEffect]

    def __init__(self, initial_state: states.PNState) -> None:
        self._context = states.PNContext()
        self._current_state = initial_state(self._context)
        self._listeners = {}
        self._effect_list = []
        self._dispatcher = Dispatcher()

    def get_state_name(self):
        return self._current_state.__class__.__name__

    def trigger(self, event: events.PNEvent) -> states.PNTransition:
        if event.get_name() in self._current_state._transitions:
            effect = self._current_state.on_exit()
            if effect:
                self._effect_list.append(effect)

            transition: states.PNTransition = self._current_state.on(event, self._context)

            self._current_state = transition.state(self._current_state.get_context())
            self._context = transition.context
            if transition.effect:
                self._effect_list.append(transition.effect)

            effect = self._current_state.on_enter(self._context)
            if effect:
                self._effect_list.append(effect)

            if transition.state:
                self._current_state = transition.state(self._context)

        else:
            # we're ignoring events unhandled
            print('unhandled event??')

        for effect in self._effect_list:
            self._dispatcher.dispatch_effect(effect)

        return self._effect_list


if __name__ == "__main__":
    machine = StateMachine(states.UnsubscribedState)
    print(f'machine initialized. Current state: {machine.get_state_name()}')
    effect = machine.trigger(events.SubscriptionChangedEvent(
        channels=['fail'], groups=[]
    ))

    machine.add_listener(effects.PNEffect, lambda x: print(f'Catch All Logger: {effect.__dict__}'))

    machine.add_listener(effects.EmitMessagesEffect, )
    effect = machine.trigger(events.DisconnectEvent())
    print(f'SubscriptionChangedEvent triggered with channels=[`fail`]. Current state: {machine.get_state_name()}')
    print(f'effect queue: {machine._effect_list}')
