from pubnub.enums import PNReconnectionPolicy
from pubnub.managers import ReconnectionManager
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


def assert_more_or_less(given, expected):
    assert expected < given < expected + 1


def test_linear_policy():
    config = PNConfiguration()
    config.subscribe_key = "test"
    config.publish_key = "test"
    config.reconnect_policy = PNReconnectionPolicy.LINEAR
    config.uuid = "test"

    pubnub = PubNub(config)
    reconnection_manager = ReconnectionManager(pubnub)

    for i in range(0, 10):
        reconnection_manager._connection_errors = i
        reconnection_manager._recalculate_interval()
        assert_more_or_less(reconnection_manager._timer_interval, 2)


def test_exponential_policy():
    config = PNConfiguration()
    config.subscribe_key = "test"
    config.publish_key = "test"
    config.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
    config.uuid = "test"

    pubnub = PubNub(config)
    reconnection_manager = ReconnectionManager(pubnub)

    expected = [2, 4, 8, 16, 32, 64, 128, 150, 150, 150]

    for i in range(0, 10):
        reconnection_manager._connection_errors = i
        reconnection_manager._recalculate_interval()
        assert_more_or_less(reconnection_manager._timer_interval, expected[i])
