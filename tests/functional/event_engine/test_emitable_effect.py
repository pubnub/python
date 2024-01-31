from unittest.mock import patch
from pubnub.event_engine import effects
from pubnub.event_engine.models import invocations
from pubnub.event_engine.dispatcher import Dispatcher
from pubnub.event_engine.models.states import UnsubscribedState
from pubnub.event_engine.statemachine import StateMachine


def test_dispatch_emit_messages_effect():
    with patch.object(effects.EmitEffect, 'emit_message') as mocked_emit_message:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(invocations.EmitMessagesInvocation(['chan']))
        mocked_emit_message.assert_called()


def test_dispatch_emit_status_effect():
    with patch.object(effects.EmitEffect, 'emit_status') as mocked_emit_status:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(invocations.EmitStatusInvocation(['chan']))
        mocked_emit_status.assert_called()
