import unittest
import logging
import pubnub

from pubnub.models.consumer.presence import PNSetStateResult, PNGetStateResult
from pubnub.pubnub import PubNub
from tests import helper
from tests.helper import pnconf_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubHereNow(unittest.TestCase):
    def test_single_channel(self):
        ch = helper.gen_channel("herenow-unit")
        pubnub = PubNub(pnconf_copy())
        state = {"name": "Alex", "count": 5}

        result = pubnub.set_state().channels(ch).state(state).sync()

        assert isinstance(result, PNSetStateResult)
        assert result.state['name'] == "Alex"
        assert result.state['count'] == 5

        result = pubnub.get_state().channels(ch).sync()

        assert isinstance(result, PNGetStateResult)
        assert result.channels[ch]['name'] == "Alex"
        assert result.channels[ch]['count'] == 5

    def test_multiple_channels(self):
        ch1 = helper.gen_channel("herenow-unit")
        ch2 = helper.gen_channel("herenow-unit")
        pubnub = PubNub(pnconf_copy())
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
