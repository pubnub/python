import unittest
import logging
import pubnub

from pubnub.models.consumer.presence import PNSetStateResult, PNGetStateResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf_copy, pn_vcr

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(unittest.TestCase):
    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/state/state_of_single_channel.yaml',
                         filter_query_parameters=['uuid'], match_on=['state_object_in_query'])
    def test_single_channel(self):
        ch = "state-native-sync-ch"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "state-native-sync-uuid"
        state = {"name": "Alex", "count": 5}

        result = pubnub.set_state().channels(ch).state(state).sync()

        assert isinstance(result, PNSetStateResult)
        assert result.state['name'] == "Alex"
        assert result.state['count'] == 5

        result = pubnub.get_state().channels(ch).sync()

        assert isinstance(result, PNGetStateResult)
        assert result.channels[ch]['name'] == "Alex"
        assert result.channels[ch]['count'] == 5

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/state/state_of_multiple_channels.yaml',
                         filter_query_parameters=['uuid'], match_on=['state_object_in_query'])
    def test_multiple_channels(self):
        ch1 = "state-native-sync-ch-1"
        ch2 = "state-native-sync-ch-2"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "state-native-sync-uuid"
        state = {"name": "Alex", "count": 5}

        result = pubnub.set_state().channels([ch1, ch2]).state(state).sync()

        assert isinstance(result, PNSetStateResult)
        assert result.state['name'] == "Alex"
        assert result.state['count'] == 5

        result = pubnub.get_state().channels([ch1, ch2]).sync()

        assert isinstance(result, PNGetStateResult)
        assert result.channels[ch1]['name'] == "Alex"
        assert result.channels[ch1]['count'] == 5
        assert result.channels[ch2]['name'] == "Alex"
        assert result.channels[ch2]['count'] == 5
