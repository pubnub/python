import pytest
import asyncio

from unittest.mock import patch
from pubnub.enums import PNReconnectionPolicy
from pubnub.event_engine import effects
from pubnub.event_engine.models import invocations
from pubnub.event_engine.dispatcher import Dispatcher
from pubnub.event_engine.models import states
from pubnub.event_engine.models.states import UnsubscribedState
from pubnub.event_engine.statemachine import StateMachine
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_env_copy


class FakeConfig:
    reconnect_policy = PNReconnectionPolicy.NONE
    RECONNECTION_INTERVAL = 1
    RECONNECTION_MIN_EXPONENTIAL_BACKOFF = 1
    RECONNECTION_MAX_EXPONENTIAL_BACKOFF = 32
    maximum_reconnection_retries = 3


class FakePN:
    def __init__(self) -> None:
        self.config = FakeConfig()


def test_dispatch_run_handshake_effect():
    with patch.object(effects.HandshakeEffect, 'run') as mocked_run:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(invocations.HandshakeInvocation(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_handshake_effect():
    with patch.object(effects.HandshakeEffect, 'stop') as mocked_stop:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(invocations.HandshakeInvocation(['chan']))
        dispatcher.dispatch_effect(invocations.CancelHandshakeInvocation())
        mocked_stop.assert_called()


def test_dispatch_run_receive_effect():
    with patch.object(effects.ReceiveMessagesEffect, 'run') as mocked_run:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(invocations.ReceiveMessagesInvocation(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_receive_effect():
    with patch.object(effects.ReceiveMessagesEffect, 'stop', ) as mocked_stop:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.dispatch_effect(invocations.ReceiveMessagesInvocation(['chan']))
        dispatcher.dispatch_effect(invocations.CancelReceiveMessagesInvocation())
        mocked_stop.assert_called()


def test_dispatch_run_handshake_reconnect_effect():
    with patch.object(effects.HandshakeReconnectEffect, 'run') as mocked_run:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.set_pn(FakePN())
        dispatcher.dispatch_effect(invocations.HandshakeReconnectInvocation(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_handshake_reconnect_effect():
    with patch.object(effects.HandshakeReconnectEffect, 'stop') as mocked_stop:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.set_pn(FakePN())
        dispatcher.dispatch_effect(invocations.HandshakeReconnectInvocation(['chan']))
        dispatcher.dispatch_effect(invocations.CancelHandshakeReconnectInvocation())
        mocked_stop.assert_called()


def test_dispatch_run_receive_reconnect_effect():
    with patch.object(effects.ReceiveReconnectEffect, 'run') as mocked_run:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.set_pn(FakePN())
        dispatcher.dispatch_effect(invocations.ReceiveReconnectInvocation(['chan']))
        mocked_run.assert_called()


def test_dispatch_stop_receive_reconnect_effect():
    with patch.object(effects.ReceiveReconnectEffect, 'stop') as mocked_stop:
        dispatcher = Dispatcher(StateMachine(UnsubscribedState))
        dispatcher.set_pn(FakePN())
        dispatcher.dispatch_effect(invocations.ReceiveReconnectInvocation(['chan']))
        dispatcher.dispatch_effect(invocations.CancelReceiveReconnectInvocation())
        mocked_stop.assert_called()


@pytest.mark.asyncio
async def test_cancel_effect():
    pubnub = PubNubAsyncio(pnconf_env_copy())
    event_engine = StateMachine(states.HeartbeatInactiveState, name="presence")
    managed_effects_factory = effects.EffectFactory(pubnub, event_engine)
    managed_wait_effect = managed_effects_factory.create(invocation=invocations.HeartbeatWaitInvocation(10))
    managed_wait_effect.run()
    await asyncio.sleep(1)
    managed_wait_effect.stop()
    await pubnub.stop()
