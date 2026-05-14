from unittest.mock import patch

from pubnub.enums import PNReconnectionPolicy
from pubnub.event_engine.effects import ReconnectEffect, HeartbeatDelayedEffect
from pubnub.event_engine.models import invocations
from pubnub.event_engine.models.states import UnsubscribedState
from pubnub.event_engine.statemachine import StateMachine
from pubnub.managers import LinearDelay, ExponentialDelay


class FakeConfig:
    def __init__(self, **kwargs):
        self.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
        self.reconnection_interval = None
        self.maximum_reconnection_interval = None
        self.maximum_reconnection_retries = None
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakePN:
    def __init__(self, **config_kwargs):
        self.config = FakeConfig(**config_kwargs)


def make_reconnect_effect(effect_cls, **config_kwargs):
    pn = FakePN(**config_kwargs)
    engine = StateMachine(UnsubscribedState)
    invocation = invocations.HandshakeReconnectInvocation(['ch'])
    return effect_cls(pn, engine, invocation)


# ---------------------------------------------------------------------------
# ReconnectEffect.calculate_reconnection_delay
# ---------------------------------------------------------------------------

class TestReconnectEffectDelay:
    def test_exponential_default(self):
        effect = make_reconnect_effect(ReconnectEffect)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(0) == 2.0
            assert effect.calculate_reconnection_delay(3) == 16.0

    def test_exponential_custom_minimum(self):
        effect = make_reconnect_effect(ReconnectEffect, reconnection_interval=3)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(0) == 3.0
            assert effect.calculate_reconnection_delay(1) == 6.0
            assert effect.calculate_reconnection_delay(2) == 12.0

    def test_exponential_custom_maximum(self):
        effect = make_reconnect_effect(ReconnectEffect, maximum_reconnection_interval=20)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(5) == 20.0

    def test_exponential_custom_minimum_and_maximum(self):
        effect = make_reconnect_effect(ReconnectEffect,
                                       reconnection_interval=1, maximum_reconnection_interval=10)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(0) == 1.0
            assert effect.calculate_reconnection_delay(3) == 8.0
            assert effect.calculate_reconnection_delay(5) == 10.0

    def test_linear_default(self):
        effect = make_reconnect_effect(ReconnectEffect,
                                       reconnect_policy=PNReconnectionPolicy.LINEAR)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(0) == 2.0
            assert effect.calculate_reconnection_delay(5) == 2.0

    def test_linear_custom_delay(self):
        effect = make_reconnect_effect(ReconnectEffect,
                                       reconnect_policy=PNReconnectionPolicy.LINEAR,
                                       reconnection_interval=5)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(0) == 5.0
            assert effect.calculate_reconnection_delay(5) == 5.0


# ---------------------------------------------------------------------------
# ReconnectEffect._should_give_up
# ---------------------------------------------------------------------------

class TestReconnectEffectShouldGiveUp:
    def test_none_policy_gives_up_immediately(self):
        effect = make_reconnect_effect(ReconnectEffect,
                                       reconnect_policy=PNReconnectionPolicy.NONE)
        assert effect._should_give_up(0) is True

    def test_unlimited_retries(self):
        effect = make_reconnect_effect(ReconnectEffect, maximum_reconnection_retries=-1)
        assert effect._should_give_up(9999) is False

    def test_exponential_default_limit(self):
        effect = make_reconnect_effect(ReconnectEffect)
        assert effect._should_give_up(ExponentialDelay.MAX_RETRIES) is False
        assert effect._should_give_up(ExponentialDelay.MAX_RETRIES + 1) is True

    def test_linear_default_limit(self):
        effect = make_reconnect_effect(ReconnectEffect,
                                       reconnect_policy=PNReconnectionPolicy.LINEAR)
        assert effect._should_give_up(LinearDelay.MAX_RETRIES) is False
        assert effect._should_give_up(LinearDelay.MAX_RETRIES + 1) is True

    def test_user_limit_higher_than_policy(self):
        effect = make_reconnect_effect(ReconnectEffect, maximum_reconnection_retries=20)
        assert effect._should_give_up(ExponentialDelay.MAX_RETRIES + 1) is False
        assert effect._should_give_up(20) is False
        assert effect._should_give_up(21) is True

    def test_user_limit_lower_than_policy(self):
        effect = make_reconnect_effect(ReconnectEffect, maximum_reconnection_retries=3)
        assert effect._should_give_up(3) is False
        assert effect._should_give_up(4) is True


# ---------------------------------------------------------------------------
# HeartbeatDelayedEffect.calculate_reconnection_delay
# ---------------------------------------------------------------------------

class TestHeartbeatDelayedEffectDelay:
    def test_exponential_default(self):
        effect = make_reconnect_effect(HeartbeatDelayedEffect)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(0) == 2.0
            assert effect.calculate_reconnection_delay(3) == 16.0

    def test_exponential_custom_minimum(self):
        effect = make_reconnect_effect(HeartbeatDelayedEffect, reconnection_interval=3)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(0) == 3.0
            assert effect.calculate_reconnection_delay(1) == 6.0

    def test_exponential_custom_maximum(self):
        effect = make_reconnect_effect(HeartbeatDelayedEffect, maximum_reconnection_interval=20)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(5) == 20.0

    def test_linear_default(self):
        effect = make_reconnect_effect(HeartbeatDelayedEffect,
                                       reconnect_policy=PNReconnectionPolicy.LINEAR)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(0) == 2.0

    def test_linear_custom_delay(self):
        effect = make_reconnect_effect(HeartbeatDelayedEffect,
                                       reconnect_policy=PNReconnectionPolicy.LINEAR,
                                       reconnection_interval=5)
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert effect.calculate_reconnection_delay(0) == 5.0


# ---------------------------------------------------------------------------
# HeartbeatDelayedEffect._should_give_up
# ---------------------------------------------------------------------------

class TestHeartbeatDelayedEffectShouldGiveUp:
    def test_none_policy_gives_up_immediately(self):
        effect = make_reconnect_effect(HeartbeatDelayedEffect,
                                       reconnect_policy=PNReconnectionPolicy.NONE)
        assert effect._should_give_up(0) is True

    def test_unlimited_retries(self):
        effect = make_reconnect_effect(HeartbeatDelayedEffect, maximum_reconnection_retries=-1)
        assert effect._should_give_up(9999) is False

    def test_user_limit_higher_than_policy(self):
        effect = make_reconnect_effect(HeartbeatDelayedEffect, maximum_reconnection_retries=20)
        assert effect._should_give_up(ExponentialDelay.MAX_RETRIES + 1) is False
        assert effect._should_give_up(21) is True
