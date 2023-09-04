import logging

from typing import List, Optional

from pubnub.event_engine.models import effects, events, states
from pubnub.event_engine.dispatcher import Dispatcher


class StateMachine:
    _current_state: states.PNState
    _context: states.PNContext
    _effect_list: List[effects.PNEffect]
    _enabled: bool

    def __init__(self, initial_state: states.PNState, dispatcher_class: Optional[Dispatcher] = None) -> None:
        self._context = states.PNContext()
        self._current_state = initial_state(self._context)
        self._listeners = {}
        self._effect_list = []
        if dispatcher_class is None:
            dispatcher_class = Dispatcher
        self._dispatcher = dispatcher_class(self)
        self._enabled = True

    def get_state_name(self):
        return self._current_state.__class__.__name__

    def get_context(self) -> states.PNContext:
        return self._current_state._context

    def get_dispatcher(self) -> Dispatcher:
        return self._dispatcher

    def trigger(self, event: events.PNEvent) -> states.PNTransition:
        logging.debug(f'Triggered {event.__class__.__name__}({event.__dict__}) on {self.get_state_name()}')
        if not self._enabled:
            logging.error('EventEngine is not enabled')
            return False
        if event.get_name() in self._current_state._transitions:
            self._effect_list.clear()
            effect = self._current_state.on_exit()
            logging.debug(f'On exit effect: {effect.__class__.__name__}')

            if effect:
                self._effect_list.append(effect)

            transition: states.PNTransition = self._current_state.on(event, self._context)

            self._current_state = transition.state(self._current_state.get_context())

            self._context = transition.context
            if transition.effect:
                if isinstance(transition.effect, list):
                    logging.debug('unpacking list')
                    for effect in transition.effect:
                        logging.debug(f'Transition effect: {effect.__class__.__name__}')
                        self._effect_list.append(effect)
                else:
                    logging.debug(f'Transition effect: {transition.effect.__class__.__name__}')
                    self._effect_list.append(transition.effect)

            effect = self._current_state.on_enter(self._context)
            if effect:
                logging.debug(f'On enter effect: {effect.__class__.__name__}')
                self._effect_list.append(effect)

        else:
            # we're ignoring events unhandled
            logging.debug(f'unhandled event?? {event.__class__.__name__} in {self._current_state.__class__.__name__}')
            self.stop()

        self.dispatch_effects()

    def dispatch_effects(self):
        for effect in self._effect_list:
            logging.debug(f'dispatching {effect.__class__.__name__} {id(effect)}')
            self._dispatcher.dispatch_effect(effect)

        self._effect_list.clear()

    def stop(self):
        self._enabled = False


""" TODO: Remove before prodction """
if __name__ == "__main__":
    machine = StateMachine(states.UnsubscribedState)
    logging.debug(f'machine initialized. Current state: {machine.get_state_name()}')
    effect = machine.trigger(events.SubscriptionChangedEvent(
        channels=['fail'], groups=[]
    ))

    machine.add_listener(effects.PNEffect, lambda x: logging.debug(f'Catch All Logger: {effect.__dict__}'))

    machine.add_listener(effects.EmitMessagesEffect, )
    effect = machine.trigger(events.DisconnectEvent())
    logging.debug(f'SubscriptionChangedEvent triggered with channels=[`fail`].  Curr state: {machine.get_state_name()}')
    logging.debug(f'effect queue: {machine._effect_list}')
