import logging
import unittest

import pubnub
from pubnub.models.consumer.presence import PNSetStateResult, PNGetStateResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf_copy, pnconf_pam_copy
from tests.integrational.vcr_helper import pn_vcr

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(unittest.TestCase):
    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/state/state_of_single_channel.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'], match_on=['state_object_in_query'])
    def test_single_channel(self):
        ch = "state-native-sync-ch"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "state-native-sync-uuid"
        state = {"name": "Alex", "count": 5}

        envelope = pubnub.set_state().channels(ch).state(state).sync()

        assert isinstance(envelope.result, PNSetStateResult)
        assert envelope.result.state['name'] == "Alex"
        assert envelope.result.state['count'] == 5

        envelope = pubnub.get_state().channels(ch).sync()

        assert isinstance(envelope.result, PNGetStateResult)
        assert envelope.result.channels[ch]['name'] == "Alex"
        assert envelope.result.channels[ch]['count'] == 5

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/state/state_of_multiple_channels.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'], match_on=['state_object_in_query'])
    def test_multiple_channels(self):
        ch1 = "state-native-sync-ch-1"
        ch2 = "state-native-sync-ch-2"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "state-native-sync-uuid"
        state = {"name": "Alex", "count": 5}

        envelope = pubnub.set_state().channels([ch1, ch2]).state(state).sync()

        assert isinstance(envelope.result, PNSetStateResult)
        assert envelope.result.state['name'] == "Alex"
        assert envelope.result.state['count'] == 5

        envelope = pubnub.get_state().channels([ch1, ch2]).sync()

        assert isinstance(envelope.result, PNGetStateResult)
        assert envelope.result.channels[ch1]['name'] == "Alex"
        assert envelope.result.channels[ch1]['count'] == 5
        assert envelope.result.channels[ch2]['name'] == "Alex"
        assert envelope.result.channels[ch2]['count'] == 5

    def test_super_call(self):
        ch1 = "state-tornado-ch1"
        ch2 = "state-tornado-ch2"
        pnconf = pnconf_pam_copy()
        pubnub = PubNub(pnconf)
        pubnub.config.uuid = 'test-state-native-uuid-|.*$'
        state = {"name": "Alex", "count": 5}

        env = pubnub.set_state() \
            .channels([ch1, ch2]) \
            .state(state) \
            .sync()

        assert env.result.state['name'] == "Alex"
        assert env.result.state['count'] == 5

        env = pubnub.get_state() \
            .channels([ch1, ch2]) \
            .sync()

        assert env.result.channels[ch1]['name'] == "Alex"
        assert env.result.channels[ch2]['name'] == "Alex"
        assert env.result.channels[ch1]['count'] == 5
        assert env.result.channels[ch2]['count'] == 5
