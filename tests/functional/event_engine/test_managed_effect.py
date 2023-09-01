from unittest.mock import patch
from pubnub.enums import PNReconnectionPolicy
from pubnub.event_engine import manage_effects
from pubnub.event_engine.models import effects
from pubnub.event_engine.dispatcher import Dispatcher
from pubnub.event_engine.models.states import UnsubscribedState
from pubnub.event_engine.statemachine import StateMachine


class FakeConfig:
    reconnect_policy = PNReconnectionPolicy.NONE
    RECONNECTION_INTERVAL = 1
    RECONNECTION_MIN_EXPONENTIAL_BACKOFF = 1
    RECONNECTION_MAX_EXPONENTIAL_BACKOFF = 32


class FakePN:
    def __init__(self) -> None:
        self.config = FakeConfig()


def test_dispatch_run_handshake_effect():
    with patch.object(manage_effects.ManageHandshakeEffect, 'run') as mocked_run:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(effects.HandshakeEffect(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_handshake_effect():
    with patch.object(manage_effects.ManageHandshakeEffect, 'stop') as mocked_stop:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(effects.HandshakeEffect(['chan']))
        dispatcher.dispatch_effect(effects.CancelHandshakeEffect())
        mocked_stop.assert_called()


def test_dispatch_run_receive_effect():
    with patch.object(manage_effects.ManagedReceiveMessagesEffect, 'run') as mocked_run:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(effects.ReceiveMessagesEffect(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_receive_effect():
    with patch.object(manage_effects.ManagedReceiveMessagesEffect, 'stop', ) as mocked_stop:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(effects.ReceiveMessagesEffect(['chan']))
        dispatcher.dispatch_effect(effects.CancelReceiveMessagesEffect())
        mocked_stop.assert_called()


def test_dispatch_run_handshake_reconnect_effect():
    with patch.object(manage_effects.ManagedHandshakeReconnectEffect, 'run') as mocked_run:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.set_pn(FakePN())
        dispatcher.dispatch_effect(effects.HandshakeReconnectEffect(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_handshake_reconnect_effect():
    with patch.object(manage_effects.ManagedHandshakeReconnectEffect, 'stop') as mocked_stop:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.set_pn(FakePN())
        dispatcher.dispatch_effect(effects.HandshakeReconnectEffect(['chan']))
        dispatcher.dispatch_effect(effects.CancelHandshakeReconnectEffect())
        mocked_stop.assert_called()


def test_dispatch_run_receive_reconnect_effect():
    with patch.object(manage_effects.ManagedEffect, 'run') as mocked_run:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(effects.ReceiveReconnectEffect(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_receive_reconnect_effect():
    with patch.object(manage_effects.ManagedEffect, 'stop') as mocked_stop:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(effects.ReceiveReconnectEffect(['chan']))
        dispatcher.dispatch_effect(effects.CancelReceiveReconnectEffect())
        mocked_stop.assert_called()
