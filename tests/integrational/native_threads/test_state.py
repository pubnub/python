import unittest
import logging
import pubnub
import threading

from pubnub.models.consumer.presence import PNSetStateResult, PNGetStateResult
from pubnub.pubnub import PubNub
from tests import helper
from tests.helper import pnconf_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def test_single_channel(self):
        ch = helper.gen_channel("herenow-unit")
        pubnub = PubNub(pnconf_copy())
        state = {"name": "Alex", "count": 5}

        pubnub.set_state() \
            .channels(ch) \
            .state(state) \
            .async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNSetStateResult)
        assert self.response.state['name'] == "Alex"
        assert self.response.state['count'] == 5

        self.event.clear()
        pubnub.get_state() \
            .channels(ch) \
            .async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNGetStateResult)
        assert self.response.channels[ch]['name'] == "Alex"
        assert self.response.channels[ch]['count'] == 5

    def test_multiple_channels(self):
        ch1 = helper.gen_channel("herenow-unit")
        ch2 = helper.gen_channel("herenow-unit")
        pubnub = PubNub(pnconf_copy())
        state = {"name": "Alex", "count": 5}

        pubnub.set_state() \
            .channels([ch1, ch2]) \
            .state(state) \
            .async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNSetStateResult)
        assert self.response.state['name'] == "Alex"
        assert self.response.state['count'] == 5

        self.event.clear()
        pubnub.get_state() \
            .channels([ch1, ch2]) \
            .async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNGetStateResult)
        assert self.response.channels[ch1]['name'] == "Alex"
        assert self.response.channels[ch1]['count'] == 5
        assert self.response.channels[ch2]['name'] == "Alex"
        assert self.response.channels[ch2]['count'] == 5
