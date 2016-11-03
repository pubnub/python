import twisted

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial import unittest
from twisted.web.client import HTTPConnectionPool

from pubnub.models.consumer.channel_group import PNChannelGroupsAddChannelResult, PNChannelGroupsListResult, \
    PNChannelGroupsRemoveChannelResult
from pubnub.pubnub_twisted import PubNubTwisted

from tests.helper import pnconf
from tests.integrational.vcr_helper import pn_vcr

twisted.internet.base.DelayedCall.debug = True


class CGTestCase(unittest.TestCase):
    def setUp(self):
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.pubnub = PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)

    def tearDown(self):
        return self.pool.closeCachedConnections()

    def assert_valid_cg_envelope(self, envelope, type):
        self.assertIsInstance(envelope.result, type)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/groups/add_single_channel.yaml',
        filter_query_parameters=['uuid'])
    def test_adding_channel(self):
        channel = 'cgttc'
        group = 'cgttg'

        envelope = yield self.pubnub.add_channel_to_channel_group() \
            .channels(channel).channel_group(group).deferred()

        self.assert_valid_cg_envelope(envelope, PNChannelGroupsAddChannelResult)

        returnValue(envelope)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/groups/remove_single_channel.yaml',
        filter_query_parameters=['uuid'])
    def test_removing_channel(self):
        channel = 'cgttc'
        group = 'cgttg'

        envelope = yield self.pubnub.remove_channel_from_channel_group() \
            .channels(channel).channel_group(group).deferred()

        self.assert_valid_cg_envelope(envelope, PNChannelGroupsRemoveChannelResult)

        returnValue(envelope)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/groups/add_channels.yaml',
        filter_query_parameters=['uuid'])
    def test_adding_channels(self):
        channel = ['cgttc0', 'cgttc1']
        group = 'cgttg'

        envelope = yield self.pubnub.add_channel_to_channel_group() \
            .channels(channel).channel_group(group).deferred()

        self.assert_valid_cg_envelope(envelope, PNChannelGroupsAddChannelResult)

        returnValue(envelope)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/groups/remove_channels.yaml',
        filter_query_parameters=['uuid'])
    def test_removing_channels(self):
        channel = ['cgttc0', 'cgttc1']
        group = 'cgttg'

        envelope = yield self.pubnub.remove_channel_from_channel_group() \
            .channels(channel).channel_group(group).deferred()

        self.assert_valid_cg_envelope(envelope, PNChannelGroupsRemoveChannelResult)

        returnValue(envelope)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/groups/list_channels.yaml',
        filter_query_parameters=['uuid'])
    def test_list_channels(self):
        group = 'cgttg'

        envelope = yield self.pubnub.list_channels_in_channel_group() \
            .channel_group(group).deferred()

        self.assert_valid_cg_envelope(envelope, PNChannelGroupsListResult)

        returnValue(envelope)
