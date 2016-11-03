import twisted

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial import unittest
from twisted.web.client import HTTPConnectionPool

from pubnub.models.consumer.presence import PNHereNowResult

from pubnub.pubnub_twisted import PubNubTwisted, TwistedEnvelope

from tests.helper import pnconf
from tests.integrational.vcr_helper import pn_vcr

twisted.internet.base.DelayedCall.debug = True

channel = 'twisted-test'
channels = 'twisted-test-1', 'twisted-test-1'


class HereNowTest(unittest.TestCase):
    def setUp(self):
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.pubnub = PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)

    def tearDown(self):
        return self.pool.closeCachedConnections()

    class PNHereNowChannelData(object):
        def __init__(self, channel_name, occupancy, occupants):
            self.channel_name = channel_name
            self.occupancy = occupancy
            self.occupants = occupants

    def assert_valid_here_now_envelope(self, envelope, result_channels):
        def get_uuids(here_now_channel_data):
            return [here_now_channel_data.channel_name,
                    here_now_channel_data.occupancy,
                    map(lambda x: x.uuid, here_now_channel_data.occupants)]

        self.assertIsInstance(envelope, TwistedEnvelope)
        self.assertIsInstance(envelope.result, PNHereNowResult)
        self.assertEqual(map(get_uuids, envelope.result.channels), result_channels)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/here_now/global.yaml',
        filter_query_parameters=['uuid'])
    def test_global_here_now(self):
        envelope = yield self.pubnub.here_now() \
            .include_uuids(True) \
            .deferred()

        self.assert_valid_here_now_envelope(envelope,
                                            [[u'twisted-test-1', 1, [u'00de2586-7ad8-4955-b5f6-87cae3215d02']],
                                             [u'twisted-test', 1, [u'00de2586-7ad8-4955-b5f6-87cae3215d02']]])
        returnValue(envelope)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/here_now/single.yaml',
        filter_query_parameters=['uuid'])
    def test_here_now_single_channel(self):
        envelope = yield self.pubnub.here_now() \
            .channels(channel) \
            .include_uuids(True) \
            .deferred()

        self.assert_valid_here_now_envelope(envelope, [['twisted-test', 1, [u'00de2586-7ad8-4955-b5f6-87cae3215d02']]])
        returnValue(envelope)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/here_now/multiple.yaml',
        filter_query_parameters=['uuid'])
    def test_here_now_multiple_channels(self):
        envelope = yield self.pubnub.here_now() \
            .channels(channels) \
            .include_uuids(True) \
            .deferred()

        self.assert_valid_here_now_envelope(envelope,
                                            [[u'twisted-test-1', 1, [u'00de2586-7ad8-4955-b5f6-87cae3215d02']]])
        returnValue(envelope)
