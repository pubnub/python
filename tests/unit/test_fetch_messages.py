from random import randrange

from pubnub.pubnub import PubNub
from tests.helper import pnconf_file_copy

pubnub = PubNub(pnconf_file_copy())

MAX_FOR_FETCH_MESSAGES = 100
MULTIPLE_CHANNELS_MAX_FOR_FETCH_MESSAGES = 25
MAX_FOR_FETCH_MESSAGES_WITH_ACTIONS = 25
EXPECTED_SINGLE_CHANNEL_DEFAULT_MESSAGES = 100
EXPECTED_MULTIPLE_CHANNEL_DEFAULT_MESSAGES = 25
EXPECTED_DEFAULT_MESSAGES_WITH_ACTIONS = 25


class TestFetchMessages:
    def test_single_channel_always_pass_max_when_in_bounds(self):
        # given
        expected_max_value = randrange(1, MAX_FOR_FETCH_MESSAGES + 1)

        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels("channel1")\
            .count(expected_max_value)

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == expected_max_value

    def test_single_channel_always_pass_default_when_non_positive(self):
        # given
        expected_max_value = randrange(-100, 1)

        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels("channel1").count(expected_max_value)

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == EXPECTED_SINGLE_CHANNEL_DEFAULT_MESSAGES

    def test_single_channel_always_pass_default_when_not_specified(self):
        # given
        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels("channel1")

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == EXPECTED_SINGLE_CHANNEL_DEFAULT_MESSAGES

    def test_single_channel_pass_default_when_max_exceeds(self):
        # given
        expected_max_value = randrange(MAX_FOR_FETCH_MESSAGES + 1, 1000)

        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels("channel1").count(expected_max_value)

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == EXPECTED_SINGLE_CHANNEL_DEFAULT_MESSAGES

    def test_multiple_channels_always_pass_max_when_in_bounds(self):
        # given
        expected_max_value = randrange(1, MULTIPLE_CHANNELS_MAX_FOR_FETCH_MESSAGES + 1)

        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels(["channel1", "channel2"]).count(expected_max_value)

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == expected_max_value

    def test_multiple_channels_always_pass_default_when_non_positive(self):
        # given
        expected_max_value = randrange(-100, 1)

        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels(["channel1", "channel2"]).count(expected_max_value)

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == EXPECTED_MULTIPLE_CHANNEL_DEFAULT_MESSAGES

    def test_multiple_channels_always_pass_default_when_not_specified(self):
        # given
        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels(["channel1", "channel2"])

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == EXPECTED_MULTIPLE_CHANNEL_DEFAULT_MESSAGES

    def test_multiple_channels_pass_default_when_max_exceeds(self):
        # given
        expected_max_value = randrange(MULTIPLE_CHANNELS_MAX_FOR_FETCH_MESSAGES + 1, 1000)

        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels(["channel1", "channel2"]).count(expected_max_value)

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == EXPECTED_MULTIPLE_CHANNEL_DEFAULT_MESSAGES

    def test_single_channel_with_actions_pass_when_in_bounds(self):
        # given
        expected_max_value = randrange(1, MAX_FOR_FETCH_MESSAGES_WITH_ACTIONS + 1)

        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels("channel1").count(expected_max_value).include_message_actions(True)

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == expected_max_value

    def test_single_channel_with_actions_pass_default_when_not_specified(self):
        # given
        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels("channel1").include_message_actions(True)

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == EXPECTED_DEFAULT_MESSAGES_WITH_ACTIONS

    def test_single_channel_with_actions_pass_default_when_max_exceeds(self):
        # given
        expected_max_value = randrange(MAX_FOR_FETCH_MESSAGES_WITH_ACTIONS + 1, 1000)

        fetch_messages_endpoint_under_test = pubnub.fetch_messages()
        fetch_messages_endpoint_under_test.channels("channel1").count(expected_max_value).include_message_actions(True)

        # when
        fetch_messages_endpoint_under_test.validate_params()

        # then
        assert fetch_messages_endpoint_under_test._count == EXPECTED_DEFAULT_MESSAGES_WITH_ACTIONS
