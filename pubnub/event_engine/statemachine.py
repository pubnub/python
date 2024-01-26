import logging

from typing import List, Optional

from pubnub.event_engine.models import effects, events, states
from pubnub.event_engine.dispatcher import Dispatcher


class StateMachine:
    _current_state: states.PNState
    _context: states.PNContext
    _effect_list: List[effects.PNEffect]
    _enabled: bool

    def __init__(self, initial_state: states.PNState, dispatcher_class: Optional[Dispatcher] = None,
                 name: str = None) -> None:
        self._context = states.PNContext()
        self._current_state = initial_state(self._context)
        self._listeners = {}
        self._effect_list = []
        if dispatcher_class is None:
            dispatcher_class = Dispatcher
        self._dispatcher = dispatcher_class(self)
        self._enabled = True
        self._name = name
        self.logger = logging.getLogger("pubnub" if not name else f"pubnub.{name}")

    def __del__(self):
        self.logger.debug('Shutting down StateMachine')
        self._enabled = False

    def get_state_name(self):
        return self._current_state.__class__.__name__

    def get_context(self) -> states.PNContext:
        return self._current_state._context

    def get_dispatcher(self) -> Dispatcher:
        return self._dispatcher

    def trigger(self, event: events.PNEvent) -> states.PNTransition:
        self.logger.debug(f'Current State: {self.get_state_name()}')
        self.logger.debug(f'Triggered event: {event.__class__.__name__}({event.__dict__}) on {self.get_state_name()}')

        if not self._enabled:
            self.logger.error('EventEngine is not enabled')
            return False

        if event.get_name() in self._current_state._transitions:
            self._effect_list.clear()
            effect = self._current_state.on_exit()

            if effect:
                self.logger.debug(f'Invoke effect: {effect.__class__.__name__}')
                self._effect_list.append(effect)

            transition: states.PNTransition = self._current_state.on(event, self._context)
            self._current_state = transition.state(self._current_state.get_context())
            self._context = transition.context

            if transition.effect:
                if isinstance(transition.effect, list):
                    self.logger.debug('unpacking list')
                    for effect in transition.effect:
                        self.logger.debug(f'Invoke effect: {effect.__class__.__name__}')
                        self._effect_list.append(effect)
                else:
                    self.logger.debug(f'Invoke effect: {transition.effect.__class__.__name__}')
                    self._effect_list.append(transition.effect)

            effect = self._current_state.on_enter(self._context)

            if effect:
                self.logger.debug(f'Invoke effect: {effect.__class__.__name__}')
                self._effect_list.append(effect)

        else:
            message = f'Unhandled event: {event.__class__.__name__} in {self._current_state.__class__.__name__}'
            self.logger.warning(message)
            self.stop()

        self.dispatch_effects()

    def dispatch_effects(self):
        for effect in self._effect_list:
            self.logger.debug(f'Dispatching {effect.__class__.__name__} {id(effect)}')
            self._dispatcher.dispatch_effect(effect)

        self._effect_list.clear()

    def stop(self):
        self._enabled = False

    @property
    def name(self):
        return self._name
