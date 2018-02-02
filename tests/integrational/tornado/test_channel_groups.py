import tornado
from tornado import gen
from tornado.testing import AsyncTestCase

from pubnub.models.consumer.channel_group import PNChannelGroupsAddChannelResult, PNChannelGroupsListResult, \
    PNChannelGroupsRemoveChannelResult, PNChannelGroupsRemoveGroupResult
from pubnub.pubnub_tornado import PubNubTornado
from tests.helper import pnconf
from tests.integrational.tornado.vcr_tornado_decorator import use_cassette_and_stub_time_sleep


class TestChannelGroups(AsyncTestCase):
    def setUp(self):
        super(TestChannelGroups, self).setUp()
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/groups/add_remove_single_channel.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_cg'])
    @tornado.testing.gen_test
    def test_add_remove_single_channel(self):
        ch = "channel-groups-tornado-ch"
        gr = "channel-groups-tornado-cg"

        # add
        env = yield self.pubnub.add_channel_to_channel_group() \
            .channels(ch).channel_group(gr).future()

        assert isinstance(env.result, PNChannelGroupsAddChannelResult)

        yield gen.sleep(1)

        # list
        env = yield self.pubnub.list_channels_in_channel_group().channel_group(gr).future()

        assert isinstance(env.result, PNChannelGroupsListResult)
        assert len(env.result.channels) == 1
        assert env.result.channels[0] == ch

        # remove
        env = yield self.pubnub.remove_channel_from_channel_group() \
            .channels(ch).channel_group(gr).future()

        assert isinstance(env.result, PNChannelGroupsRemoveChannelResult)

        yield gen.sleep(1)

        # list
        env = yield self.pubnub.list_channels_in_channel_group().channel_group(gr).future()
        assert isinstance(env.result, PNChannelGroupsListResult)
        assert len(env.result.channels) == 0

        self.pubnub.stop()
        self.stop()

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/groups/add_remove_multiple_channel.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_cg'])
    @tornado.testing.gen_test
    def test_add_remove_multiple_channels(self):
        ch1 = "channel-groups-tornado-ch1"
        ch2 = "channel-groups-tornado-ch2"
        gr = "channel-groups-tornado-cg"

        # add
        env = yield self.pubnub.add_channel_to_channel_group() \
            .channels([ch1, ch2]).channel_group(gr).future()

        assert isinstance(env.result, PNChannelGroupsAddChannelResult)

        yield gen.sleep(1)

        # list
        env = yield self.pubnub.list_channels_in_channel_group().channel_group(gr).future()
        assert isinstance(env.result, PNChannelGroupsListResult)
        assert len(env.result.channels) == 2
        assert ch1 in env.result.channels
        assert ch2 in env.result.channels

        # remove
        env = yield self.pubnub.remove_channel_from_channel_group() \
            .channels([ch1, ch2]).channel_group(gr).future()

        assert isinstance(env.result, PNChannelGroupsRemoveChannelResult)

        yield gen.sleep(1)

        # list
        env = yield self.pubnub.list_channels_in_channel_group().channel_group(gr).future()
        assert isinstance(env.result, PNChannelGroupsListResult)
        assert len(env.result.channels) == 0

        self.pubnub.stop()
        self.stop()

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/groups/add_channel_remove_group.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_cg'])
    @tornado.testing.gen_test
    def test_add_channel_remove_group(self):
        ch = "channel-groups-tornado-ch"
        gr = "channel-groups-tornado-cg"

        # add
        env = yield self.pubnub.add_channel_to_channel_group() \
            .channels(ch).channel_group(gr).future()

        assert isinstance(env.result, PNChannelGroupsAddChannelResult)

        yield gen.sleep(1)

        # list
        env = yield self.pubnub.list_channels_in_channel_group().channel_group(gr).future()
        assert isinstance(env.result, PNChannelGroupsListResult)
        assert len(env.result.channels) == 1
        assert env.result.channels[0] == ch

        # remove group
        env = yield self.pubnub.remove_channel_group().channel_group(gr).future()

        assert isinstance(env.result, PNChannelGroupsRemoveGroupResult)

        yield gen.sleep(1)

        # list
        env = yield self.pubnub.list_channels_in_channel_group().channel_group(gr).future()
        assert isinstance(env.result, PNChannelGroupsListResult)
        assert len(env.result.channels) == 0

        self.pubnub.stop()
        self.stop()
