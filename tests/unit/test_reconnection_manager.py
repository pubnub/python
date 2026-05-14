from unittest.mock import patch

from pubnub.enums import PNReconnectionPolicy
from pubnub.managers import ReconnectionManager, LinearDelay, ExponentialDelay
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


def make_pubnub(**overrides):
    config = PNConfiguration()
    config.subscribe_key = "test"
    config.publish_key = "test"
    config.uuid = "test"
    for key, value in overrides.items():
        setattr(config, key, value)
    return PubNub(config)


def assert_delay_in_range(actual, expected_base):
    assert expected_base <= actual < expected_base + 1


# ---------------------------------------------------------------------------
# LinearDelay.calculate
# ---------------------------------------------------------------------------

class TestLinearDelayCalculate:
    def test_default_delay(self):
        with patch('pubnub.managers.random.random', return_value=0.5):
            result = LinearDelay.calculate(attempt=0)
        assert result == 2.5

    def test_custom_delay(self):
        with patch('pubnub.managers.random.random', return_value=0.5):
            result = LinearDelay.calculate(attempt=0, delay=5)
        assert result == 5.5

    def test_delay_none_uses_default(self):
        with patch('pubnub.managers.random.random', return_value=0.5):
            result = LinearDelay.calculate(attempt=3, delay=None)
        assert result == 2.5

    def test_delay_is_constant_across_attempts(self):
        with patch('pubnub.managers.random.random', return_value=0.0):
            for attempt in range(10):
                result = LinearDelay.calculate(attempt=attempt, delay=3)
                assert result == 3.0


# ---------------------------------------------------------------------------
# ExponentialDelay.calculate
# ---------------------------------------------------------------------------

class TestExponentialDelayCalculate:
    def test_default_delays(self):
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert ExponentialDelay.calculate(attempt=0) == 2.0
            assert ExponentialDelay.calculate(attempt=1) == 4.0
            assert ExponentialDelay.calculate(attempt=2) == 8.0
            assert ExponentialDelay.calculate(attempt=3) == 16.0
            assert ExponentialDelay.calculate(attempt=4) == 32.0
            assert ExponentialDelay.calculate(attempt=5) == 64.0
            assert ExponentialDelay.calculate(attempt=6) == 128.0

    def test_default_max_backoff_cap(self):
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert ExponentialDelay.calculate(attempt=7) == 150.0
            assert ExponentialDelay.calculate(attempt=10) == 150.0

    def test_custom_minimum_delay(self):
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert ExponentialDelay.calculate(attempt=0, minimum_delay=3) == 3.0
            assert ExponentialDelay.calculate(attempt=1, minimum_delay=3) == 6.0
            assert ExponentialDelay.calculate(attempt=2, minimum_delay=3) == 12.0

    def test_custom_maximum_delay(self):
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert ExponentialDelay.calculate(attempt=0, maximum_delay=10) == 2.0
            assert ExponentialDelay.calculate(attempt=3, maximum_delay=10) == 10.0
            assert ExponentialDelay.calculate(attempt=5, maximum_delay=10) == 10.0

    def test_custom_minimum_and_maximum_delay(self):
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert ExponentialDelay.calculate(attempt=0, minimum_delay=1, maximum_delay=20) == 1.0
            assert ExponentialDelay.calculate(attempt=1, minimum_delay=1, maximum_delay=20) == 2.0
            assert ExponentialDelay.calculate(attempt=4, minimum_delay=1, maximum_delay=20) == 16.0
            assert ExponentialDelay.calculate(attempt=5, minimum_delay=1, maximum_delay=20) == 20.0

    def test_none_values_use_defaults(self):
        with patch('pubnub.managers.random.random', return_value=0.0):
            assert ExponentialDelay.calculate(attempt=0, minimum_delay=None, maximum_delay=None) == 2.0

    def test_jitter_added(self):
        with patch('pubnub.managers.random.random', return_value=0.123):
            result = ExponentialDelay.calculate(attempt=0)
        assert result == 2.123


# ---------------------------------------------------------------------------
# ReconnectionManager._recalculate_interval
# ---------------------------------------------------------------------------

class TestRecalculateInterval:
    def test_linear_default_interval(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.LINEAR)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = 5
        manager._recalculate_interval()
        assert_delay_in_range(manager._timer_interval, 2)

    def test_linear_custom_interval(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.LINEAR, reconnection_interval=7)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = 0
        manager._recalculate_interval()
        assert_delay_in_range(manager._timer_interval, 7)

    def test_exponential_default_interval(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.EXPONENTIAL)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = 3
        manager._recalculate_interval()
        assert_delay_in_range(manager._timer_interval, 16)

    def test_exponential_custom_minimum(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.EXPONENTIAL, reconnection_interval=3)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = 0
        manager._recalculate_interval()
        assert_delay_in_range(manager._timer_interval, 3)

    def test_exponential_custom_maximum(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.EXPONENTIAL,
                             maximum_reconnection_interval=20)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = 5
        manager._recalculate_interval()
        assert_delay_in_range(manager._timer_interval, 20)

    def test_exponential_custom_minimum_and_maximum(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.EXPONENTIAL,
                             reconnection_interval=1, maximum_reconnection_interval=10)
        manager = ReconnectionManager(pubnub)

        manager._connection_errors = 0
        manager._recalculate_interval()
        assert_delay_in_range(manager._timer_interval, 1)

        manager._connection_errors = 3
        manager._recalculate_interval()
        assert_delay_in_range(manager._timer_interval, 8)

        manager._connection_errors = 5
        manager._recalculate_interval()
        assert_delay_in_range(manager._timer_interval, 10)


# ---------------------------------------------------------------------------
# ReconnectionManager._retry_limit_reached
# ---------------------------------------------------------------------------

class TestRetryLimitReached:
    def test_none_policy_always_reached(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.NONE)
        manager = ReconnectionManager(pubnub)
        assert manager._retry_limit_reached() is True

    def test_zero_retries_always_reached(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.LINEAR, maximum_reconnection_retries=0)
        manager = ReconnectionManager(pubnub)
        assert manager._retry_limit_reached() is True

    def test_unlimited_retries(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.LINEAR, maximum_reconnection_retries=-1)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = 9999
        assert manager._retry_limit_reached() is False

    def test_linear_default_limit(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.LINEAR)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = LinearDelay.MAX_RETRIES
        assert manager._retry_limit_reached() is False
        manager._connection_errors = LinearDelay.MAX_RETRIES + 1
        assert manager._retry_limit_reached() is True

    def test_exponential_default_limit(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.EXPONENTIAL)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = ExponentialDelay.MAX_RETRIES
        assert manager._retry_limit_reached() is False
        manager._connection_errors = ExponentialDelay.MAX_RETRIES + 1
        assert manager._retry_limit_reached() is True

    def test_user_limit_respected_when_higher_than_policy(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.EXPONENTIAL,
                             maximum_reconnection_retries=20)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = ExponentialDelay.MAX_RETRIES + 1
        assert manager._retry_limit_reached() is False
        manager._connection_errors = 20
        assert manager._retry_limit_reached() is True

    def test_user_limit_respected_when_lower_than_policy(self):
        pubnub = make_pubnub(reconnect_policy=PNReconnectionPolicy.LINEAR,
                             maximum_reconnection_retries=3)
        manager = ReconnectionManager(pubnub)
        manager._connection_errors = 2
        assert manager._retry_limit_reached() is False
        manager._connection_errors = 3
        assert manager._retry_limit_reached() is True
