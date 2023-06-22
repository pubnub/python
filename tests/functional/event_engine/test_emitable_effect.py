from unittest.mock import patch
from pubnub.event_engine import manage_effects
from pubnub.event_engine.models import effects
from pubnub.event_engine.dispatcher import Dispatcher
from pubnub.event_engine.models.states import UnsubscribedState
from pubnub.event_engine.statemachine import StateMachine


def test_dispatch_emit_messages_effect():
    with patch.object(manage_effects.EmitEffect, 'emit_message') as mocked_emit_message:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(effects.EmitMessagesEffect(['chan']))
        mocked_emit_message.assert_called()


def test_dispatch_emit_status_effect():
    with patch.object(manage_effects.EmitEffect, 'emit_status') as mocked_emit_status:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(effects.EmitStatusEffect(['chan']))
        mocked_emit_status.assert_called()
