from unittest.mock import patch
from pubnub.event_engine import effects
from pubnub.event_engine.dispatcher import Dispatcher


def test_dispatch_emit_messages_effect():
    with patch.object(effects.EmitEffect, 'emit_message') as mocked_emit_message:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.EmitMessagesEffect(['chan']))
        mocked_emit_message.assert_called()


def test_dispatch_emit_status_effect():
    with patch.object(effects.EmitEffect, 'emit_status') as mocked_emit_status:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.EmitStatusEffect(['chan']))
        mocked_emit_status.assert_called()
