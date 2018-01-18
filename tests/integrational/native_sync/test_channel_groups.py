import logging
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
    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/channel_groups/single_channel.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_cg'])
    def test_single_channel(self):
        ch = "channel-groups-native-ch"
        gr = "channel-groups-native-cg"
        pubnub = PubNub(pnconf_copy())

        # cleanup
        envelope = pubnub.remove_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsRemoveGroupResult)

        # add
        envelope = pubnub.add_channel_to_channel_group() \
            .channels(ch) \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsAddChannelResult)

        time.sleep(2)

        # list
        envelope = pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsListResult)
        assert len(envelope.result.channels) == 1
        assert envelope.result.channels[0] == ch

        # remove
        envelope = pubnub.remove_channel_from_channel_group() \
            .channels(ch) \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsRemoveChannelResult)

        time.sleep(2)

        # list
        envelope = pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsListResult)
        assert len(envelope.result.channels) == 0

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/channel_groups/add_remove_multiple_channels.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_cg'])
    def test_add_remove_multiple_channels(self):
        ch1 = "channel-groups-unit-ch1"
        ch2 = "channel-groups-unit-ch2"
        gr = "channel-groups-unit-cg"
        pubnub = PubNub(pnconf_copy())

        # cleanup
        envelope = pubnub.remove_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsRemoveGroupResult)

        # add
        envelope = pubnub.add_channel_to_channel_group() \
            .channels([ch1, ch2]) \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsAddChannelResult)

        time.sleep(1)

        # list
        envelope = pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsListResult)
        assert len(envelope.result.channels) == 2
        assert ch1 in envelope.result.channels
        assert ch2 in envelope.result.channels

        # remove
        envelope = pubnub.remove_channel_from_channel_group() \
            .channels([ch1, ch2]) \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsRemoveChannelResult)

        time.sleep(1)

        # list
        envelope = pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsListResult)
        assert len(envelope.result.channels) == 0

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/channel_groups/add_channel_remove_group.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_cg'])
    def test_add_channel_remove_group(self):
        ch = "channel-groups-unit-ch"
        gr = "channel-groups-unit-cg"
        pubnub = PubNub(pnconf_copy())

        # cleanup
        envelope = pubnub.remove_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsRemoveGroupResult)

        # add
        envelope = pubnub.add_channel_to_channel_group() \
            .channels(ch) \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsAddChannelResult)

        time.sleep(1)

        # list
        envelope = pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsListResult)
        assert len(envelope.result.channels) == 1
        assert envelope.result.channels[0] == ch

        # remove
        envelope = pubnub.remove_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsRemoveGroupResult)

        time.sleep(1)

        # list
        envelope = pubnub.list_channels_in_channel_group() \
            .channel_group(gr) \
            .sync()

        assert isinstance(envelope.result, PNChannelGroupsListResult)
        assert len(envelope.result.channels) == 0
