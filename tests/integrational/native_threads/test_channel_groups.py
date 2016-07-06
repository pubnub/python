import threading
import time
import unittest
import logging
import pubnub

from pubnub.models.consumer.channel_group import PNChannelGroupsAddChannelResult, PNChannelGroupsListResult, \
    PNChannelGroupsRemoveChannelResult, PNChannelGroupsRemoveGroupResult
from pubnub.pubnub import PubNub
from tests import helper
from tests.helper import pnconf_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubChannelGroups(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def test_single_channel(self):
        ch = helper.gen_channel("herenow-unit")
        gr = helper.gen_channel("herenow-unit")
        pubnub = PubNub(pnconf_copy())

        # add
        pubnub.add_channel_to_channel_group() \
            .channels(ch)\
            .channel_group(gr)\
            .async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNChannelGroupsAddChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group()\
            .channel_group(gr)\
            .async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 1
        assert self.response.channels[0] == ch
        self.event.clear()

        # remove
        pubnub.remove_channel_from_channel_group() \
            .channels(ch)\
            .channel_group(gr)\
            .async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsRemoveChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group()\
            .channel_group(gr)\
            .async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 0
        self.event.clear()

    def test_add_remove_multiple_channels(self):
        ch1 = helper.gen_channel("herenow-unit")
        ch2 = helper.gen_channel("herenow-unit")
        gr = helper.gen_channel("herenow-unit")
        pubnub = PubNub(pnconf_copy())

        # add
        pubnub.add_channel_to_channel_group() \
            .channels([ch1, ch2]) \
            .channel_group(gr) \
            .async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNChannelGroupsAddChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 2
        assert ch1 in self.response.channels
        assert ch2 in self.response.channels
        self.event.clear()

        # remove
        pubnub.remove_channel_from_channel_group() \
            .channels([ch1, ch2]) \
            .channel_group(gr) \
            .async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsRemoveChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 0
        self.event.clear()

    def test_add_channel_remove_group(self):
        ch = helper.gen_channel("herenow-unit")
        gr = helper.gen_channel("herenow-unit")
        pubnub = PubNub(pnconf_copy())

        # add
        pubnub.add_channel_to_channel_group() \
            .channels(ch) \
            .channel_group(gr) \
            .async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNChannelGroupsAddChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 1
        assert self.response.channels[0] == ch
        self.event.clear()

        # remove
        pubnub.remove_channel_group() \
            .channel_group(gr) \
            .async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsRemoveGroupResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 0
        self.event.clear()
