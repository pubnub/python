from copy import copy

import twisted

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial import unittest
from twisted.web.client import HTTPConnectionPool

from pubnub.models.consumer.presence import PNSetStateResult

from pubnub.pubnub_twisted import PubNubTwisted, TwistedEnvelope

from tests.helper import pnconf
from tests.integrational.vcr_helper import pn_vcr

twisted.internet.base.DelayedCall.debug = True

channel = 'twisted-test'
channels = ['twisted-test-0', 'twisted-test-1']
state = {'whatever': 'something'}


class StateTestCase(unittest.TestCase):
    def setUp(self):
        pnconf_uuid_set = copy(pnconf)
        pnconf_uuid_set.uuid = 'someuuid'
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.pubnub = PubNubTwisted(pnconf_uuid_set, reactor=reactor, pool=self.pool)

    def tearDown(self):
        return self.pool.closeCachedConnections()

    def assert_valid_state_envelope(self, envelope):
        self.assertIsInstance(envelope, TwistedEnvelope)
        self.assertIsInstance(envelope.result, PNSetStateResult)
        self.assertEqual(envelope.result.state, state)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/state/single_channel.yaml',
        filter_query_parameters=['uuid'])
    def test_state_single_channel(self):
        envelope = yield self.pubnub.set_state().channels(channel).state(state).deferred()
        self.assert_valid_state_envelope(envelope)
        returnValue(envelope)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/state/multiple_channels.yaml',
        filter_query_parameters=['uuid'])
    def test_state_multiple_channels(self):
        envelope = yield self.pubnub.set_state().channels(channels).state(state).deferred()
        self.assert_valid_state_envelope(envelope)
        returnValue(envelope)
