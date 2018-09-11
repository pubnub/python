import logging
import threading
import time
import unittest

import pubnub
from pubnub.models.consumer.channel_group import PNChannelGroupsAddChannelResult, PNChannelGroupsListResult, \
    PNChannelGroupsRemoveChannelResult, PNChannelGroupsRemoveGroupResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import use_cassette_and_stub_time_sleep_native

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubChannelGroups(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_threads/channel_groups/single_channel.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_cg'])
    def test_single_channel(self):
        ch = "channel-groups-unit-ch"
        gr = "channel-groups-unit-cg"
        pubnub = PubNub(pnconf_copy())

        # add
        pubnub.add_channel_to_channel_group() \
            .channels(ch) \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNChannelGroupsAddChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 1
        assert self.response.channels[0] == ch
        self.event.clear()

        # remove
        pubnub.remove_channel_from_channel_group() \
            .channels(ch) \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsRemoveChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 0
        self.event.clear()

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_threads/channel_groups/add_remove_multiple_channels.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_cg'])
    def test_add_remove_multiple_channels(self):
        ch1 = "channel-groups-unit-ch1"
        ch2 = "channel-groups-unit-ch2"
        gr = "channel-groups-unit-cg"
        pubnub = PubNub(pnconf_copy())

        # add
        pubnub.add_channel_to_channel_group() \
            .channels([ch1, ch2]) \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNChannelGroupsAddChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .pn_async(self.callback)

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
            .pn_async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsRemoveChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 0
        self.event.clear()

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_threads/channel_groups/add_channel_remove_group.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_cg'])
    def test_add_channel_remove_group(self):
        ch = "channel-groups-unit-ch"
        gr = "channel-groups-unit-cg"
        pubnub = PubNub(pnconf_copy())

        # add
        pubnub.add_channel_to_channel_group() \
            .channels(ch) \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNChannelGroupsAddChannelResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 1
        assert self.response.channels[0] == ch
        self.event.clear()

        # remove
        pubnub.remove_channel_group() \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsRemoveGroupResult)
        self.event.clear()

        time.sleep(1)

        # list
        pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .pn_async(self.callback)

        self.event.wait()
        assert isinstance(self.response, PNChannelGroupsListResult)
        assert len(self.response.channels) == 0
        self.event.clear()
