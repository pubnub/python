import twisted

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial import unittest
from twisted.web.client import HTTPConnectionPool

from pubnub.models.consumer.presence import PNWhereNowResult

from pubnub.pubnub_twisted import PubNubTwisted, TwistedEnvelope

from tests.helper import pnconf
from tests.integrational.vcr_helper import pn_vcr

twisted.internet.base.DelayedCall.debug = True

uuid_looking_for = '00de2586-7ad8-4955-b5f6-87cae3215d02'


class WhereNowTestCase(unittest.TestCase):
    def setUp(self):
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.pubnub = PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)

    def tearDown(self):
        return self.pool.closeCachedConnections()

    def assert_valid_where_now_envelope(self, envelope, channels):
        self.assertIsInstance(envelope, TwistedEnvelope)
        self.assertIsInstance(envelope.result, PNWhereNowResult)
        self.assertEqual(envelope.result.channels, channels)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/where_now/single.yaml',
        filter_query_parameters=['uuid'])
    def test_where_now_single_channel(self):
        envelope = yield self.pubnub.where_now().uuid(uuid_looking_for).deferred()
        self.assert_valid_where_now_envelope(envelope, [u'twisted-test-1'])
        returnValue(envelope)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/where_now/multiple.yaml',
        filter_query_parameters=['uuid'])
    def test_where_now_multiple_channels(self):
        envelope = yield self.pubnub.where_now().uuid(uuid_looking_for).deferred()
        self.assert_valid_where_now_envelope(envelope, [u'twisted-test-2', u'twisted-test-1'])
        returnValue(envelope)
