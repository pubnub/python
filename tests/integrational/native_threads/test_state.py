import logging
import threading
import unittest

import pubnub
from pubnub.models.consumer.presence import PNSetStateResult, PNGetStateResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/state/state_of_single_channel.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'], match_on=['state_object_in_query'])
    def test_single_channel(self):
        ch = "state-native-sync-ch"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "state-native-sync-uuid"
        state = {"name": "Alex", "count": 5}

        pubnub.set_state() \
            .channels(ch) \
            .state(state) \
            .pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNSetStateResult)
        assert self.response.state['name'] == "Alex"
        assert self.response.state['count'] == 5

        self.event.clear()
        pubnub.get_state() \
            .channels(ch) \
            .pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNGetStateResult)
        assert self.response.channels[ch]['name'] == "Alex"
        assert self.response.channels[ch]['count'] == 5

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/state/state_of_multiple_channels.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'], match_on=['state_object_in_query'])
    def test_multiple_channels(self):
        ch1 = "state-native-sync-ch-1"
        ch2 = "state-native-sync-ch-2"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "state-native-sync-uuid"
        state = {"name": "Alex", "count": 5}

        pubnub.set_state() \
            .channels([ch1, ch2]) \
            .state(state) \
            .pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNSetStateResult)
        assert self.response.state['name'] == "Alex"
        assert self.response.state['count'] == 5

        self.event.clear()
        pubnub.get_state() \
            .channels([ch1, ch2]) \
            .pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNGetStateResult)
        assert self.response.channels[ch1]['name'] == "Alex"
        assert self.response.channels[ch1]['count'] == 5
        assert self.response.channels[ch2]['name'] == "Alex"
        assert self.response.channels[ch2]['count'] == 5
