from unittest.mock import patch
from pubnub.event_engine import effects
from pubnub.event_engine.dispatcher import Dispatcher


def test_dispatch_run_handshake_effect():
    with patch.object(effects.ManagedEffect, 'run') as mocked_run:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.HandshakeEffect(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_handshake_effect():
    with patch.object(effects.ManagedEffect, 'stop') as mocked_stop:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.HandshakeEffect(['chan']))
        dispatcher.dispatch_effect(effects.CancelHandshakeEffect())
        mocked_stop.assert_called()


def test_dispatch_run_receive_effect():
    with patch.object(effects.ManagedEffect, 'run') as mocked_run:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.ReceiveMessagesEffect(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_receive_effect():
    with patch.object(effects.ManagedEffect, 'stop', ) as mocked_stop:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.ReceiveMessagesEffect(['chan']))
        dispatcher.dispatch_effect(effects.CancelReceiveMessagesEffect())
        mocked_stop.assert_called()


def test_dispatch_run_handshake_reconnect_effect():
    with patch.object(effects.ManagedEffect, 'run') as mocked_run:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.HandshakeReconnectEffect(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_handshake_reconnect_effect():
    with patch.object(effects.ManagedEffect, 'stop') as mocked_stop:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.HandshakeReconnectEffect(['chan']))
        dispatcher.dispatch_effect(effects.CancelHandshakeReconnectEffect())
        mocked_stop.assert_called()


def test_dispatch_run_receive_reconnect_effect():
    with patch.object(effects.ManagedEffect, 'run') as mocked_run:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.ReceiveReconnectEffect(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_receive_reconnect_effect():
    with patch.object(effects.ManagedEffect, 'stop') as mocked_stop:
        dispatcher = Dispatcher()
        dispatcher.dispatch_effect(effects.ReceiveReconnectEffect(['chan']))
        dispatcher.dispatch_effect(effects.CancelReceiveReconnectEffect())
        mocked_stop.assert_called()
