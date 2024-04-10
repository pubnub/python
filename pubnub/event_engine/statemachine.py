import logging

from typing import List, Optional

from pubnub.event_engine.models import events, invocations, states
from pubnub.event_engine.dispatcher import Dispatcher


class StateMachine:
    _current_state: states.PNState
    _context: states.PNContext
    _invocations: List[invocations.PNInvocation]
    _enabled: bool

    def __init__(self, initial_state: states.PNState, dispatcher_class: Optional[Dispatcher] = None,
                 name: Optional[str] = None) -> None:
        self._context = states.PNContext()
        self._current_state = initial_state(self._context)
        self._listeners = {}
        self._invocations = []
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
            self._invocations.clear()
            invocation = self._current_state.on_exit()

            if invocation:
                self.logger.debug(f'Invoke effect: {invocation.__class__.__name__}')
                self._invocations.append(invocation)

            transition: states.PNTransition = self._current_state.on(event, self._context)
            self._current_state = transition.state(self._current_state.get_context())
            self._context = transition.context

            if transition.invocation:
                if isinstance(transition.invocation, list):
                    self.logger.debug('unpacking list')
                    for invocation in transition.invocation:
                        self.logger.debug(f'Invoke effect: {invocation.__class__.__name__}')
                        self._invocations.append(invocation)
                else:
                    self.logger.debug(f'Invoke effect: {transition.invocation.__class__.__name__}')
                    self._invocations.append(transition.invocation)

            invocation = self._current_state.on_enter(self._context)

            if invocation:
                self.logger.debug(f'Invoke effect: {invocation.__class__.__name__}')
                self._invocations.append(invocation)

        else:
            self.logger.warning(f'Unhandled event: {event.get_name()} in {self.get_state_name()}')

        self.dispatch_effects()

    def dispatch_effects(self):
        for invocation in self._invocations:
            self.logger.debug(f'Dispatching {invocation.__class__.__name__} {invocation.__dict__} {id(invocation)}')
            self._dispatcher.dispatch_effect(invocation)

        self._invocations.clear()

    def stop(self):
        self._enabled = False

    @property
    def name(self):
        return self._name
