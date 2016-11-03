import twisted
import pytest

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial import unittest
from twisted.web.client import HTTPConnectionPool

from pubnub.exceptions import PubNubException
from pubnub.errors import PNERR_MESSAGE_MISSING, PNERR_CHANNEL_MISSING

from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pnconfiguration import PNConfiguration

from pubnub.pubnub_twisted import PubNubTwisted, TwistedEnvelope, PubNubTwistedException

from tests.helper import pnconf, pnconf_pam_copy, pnconf_enc_copy
from tests.integrational.vcr_helper import pn_vcr

twisted.internet.base.DelayedCall.debug = True

channel = 'twisted-test'


class PublishTestCase(unittest.TestCase):
    def setUp(self):
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.pubnub = PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)

    def tearDown(self):
        return self.pool.closeCachedConnections()

    # for async
    def error_envelope_asserter(self, expected_err_msg):
        def assert_error_message(envelope):
            assert envelope.status.error_data.information == expected_err_msg

        return assert_error_message

    def assert_client_error(self, publish, message):
        try:
            publish.deferred()
        except PubNubException as exception:
            self.assertTrue(message in exception.message)
        else:
            self.fail('Expected PubNubException not raised')

    def assert_client_side_error(self, envelope, expected_err_msg):
        assert envelope.status.error_data.information == expected_err_msg

    def assert_valid_publish_envelope(self, envelope):
        assert isinstance(envelope, TwistedEnvelope)
        assert isinstance(envelope.result, PNPublishResult)
        assert isinstance(envelope.status, PNStatus)
        assert envelope.result.timetoken > 0

    @inlineCallbacks
    def deferred(self, event):
        envelope = yield event.deferred()
        returnValue(envelope)

    @inlineCallbacks
    def assert_success_publish_get(self, message, meta=None):
        publish = self.pubnub.publish().channel(channel).message(message).meta(meta)
        envelope = yield self.deferred(publish)
        self.assert_valid_publish_envelope(envelope)
        returnValue(envelope)

    @inlineCallbacks
    def assert_success_encrypted_publish_get(self, message):
        pubnub = PubNubTwisted(pnconf_enc_copy())
        publish = pubnub.publish().channel(channel).message(message)
        envelope = yield self.deferred(publish)
        self.assert_valid_publish_envelope(envelope)
        returnValue(envelope)

    @inlineCallbacks
    def assert_success_publish_post(self, message):
        publish = self.pubnub.publish().channel(channel).message(message).use_post(True)
        envelope = yield self.deferred(publish)
        self.assert_valid_publish_envelope(envelope)
        returnValue(envelope)

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/publish/mixed_via_get.yaml',
        filter_query_parameters=['uuid', 'seqn'])
    def test_publish_mixed_via_get(self):
        d0 = yield self.assert_success_publish_get("hi")
        d1 = yield self.assert_success_publish_get(5)
        d2 = yield self.assert_success_publish_get(True)
        d3 = yield self.assert_success_publish_get(["hi", "hi2", "hi3"])
        returnValue([d0, d1, d2, d3])

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/publish/mixed_encrypted_via_get.yaml',
        filter_query_parameters=['uuid', 'seqn'])
    def test_publish_mixed_encrypted_via_get(self):
        d0 = yield self.assert_success_encrypted_publish_get("hi")
        d1 = yield self.assert_success_encrypted_publish_get(5)
        d2 = yield self.assert_success_encrypted_publish_get(True)
        d3 = yield self.assert_success_encrypted_publish_get(["hi", "hi2", "hi3"])
        returnValue([d0, d1, d2, d3])

    # TODO: uncomment this when vcr for post is fixed
    # @inlineCallbacks
    # @pn_vcr.use_cassette(
    #     'tests/integrational/fixtures/twisted/publish/mixed_via_post.yaml',
    #     filter_query_parameters=['uuid', 'seqn'])
    # def test_publish_mixed_via_post(self):
    #     d0 = yield self.assert_success_publish_post("hi")
    #     d1 = yield self.assert_success_publish_post(5)
    #     d2 = yield self.assert_success_publish_post(True)
    #     d3 = yield self.assert_success_publish_post(["hi", "hi2", "hi3"])
    #     returnValue([d0, d1, d2, d3])

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/publish/object_via_get.yaml',
        filter_query_parameters=['uuid', 'seqn'])
    def test_publish_object_via_get(self):
        d0 = yield self.assert_success_publish_get({"one": 2, "three": True})
        returnValue(d0)

    def test_error_missing_message(self):
        self.assert_client_error(
            self.pubnub.publish().channel(channel).message(None),
            PNERR_MESSAGE_MISSING
        )

    def test_error_missing_channel(self):
        self.assert_client_error(
            self.pubnub.publish().channel('').message('whatever'),
            PNERR_CHANNEL_MISSING
        )

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/publish/invalid_key.yaml',
        filter_query_parameters=['uuid', 'seqn'])
    def test_error_invalid_key(self):
        conf = PNConfiguration()
        conf.publish_key = "fake"
        conf.subscribe_key = "demo"
        pubnub = PubNubTwisted(conf)
        with pytest.raises(PubNubTwistedException) as exception:
            yield pubnub.publish().channel(channel).message("hey").deferred()

        self.assertEqual(exception.value.status.error_data.information,
                         "HTTP Client Error (400): [0, u'Invalid Key', u'14767989321048626']")

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/publish/forbidden.yaml',
        filter_query_parameters=['uuid', 'seqn', 'timestamp', 'signature'])
    def test_error_forbidden(self):
        pubnub = PubNubTwisted(pnconf_pam_copy())
        with pytest.raises(PubNubTwistedException) as exception:
            yield pubnub.publish().channel("not_permitted_channel").message("hey").deferred()

        self.assertEqual(exception.value.status.error_data.information,
                         "HTTP Client Error (403): {u'status': 403, u'message': u'Forbidden', u'payload':"
                         " {u'channels': [u'not_permitted_channel']}, u'service': u'Access Manager', u'error': True}")

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/publish/meta_object.yaml',
        filter_query_parameters=['uuid', 'seqn'],
        match_on=['host', 'method', 'path', 'meta_object_in_query'])
    def test_publish_with_meta(self):
        yield self.assert_success_publish_get('hi', {'a': 2, 'b': True})

    @inlineCallbacks
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/twisted/publish/do_not_store.yaml',
        filter_query_parameters=['uuid', 'seqn'])
    def test_publish_do_not_store(self):
        publish = self.pubnub.publish().channel(channel).message('whatever').should_store(False)
        envelope = yield self.deferred(publish)
        self.assert_valid_publish_envelope(envelope)
        returnValue(envelope)
