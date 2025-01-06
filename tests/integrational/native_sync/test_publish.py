import logging
import unittest
import urllib
import urllib.parse

import pubnub
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf, pnconf_demo_copy, pnconf_enc, pnconf_file_copy, pnconf_env
from tests.integrational.vcr_helper import pn_vcr
from unittest.mock import patch

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubPublish(unittest.TestCase):
    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_string_get.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_string_get(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message("hi") \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_list_get.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_list_get(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(["hi", "hi2", "hi3"]) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/publish/publish_object_get.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
        match_on=['method', 'scheme', 'host', 'port', 'object_in_path', 'query'])
    def test_publish_object_get(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message({"name": "Alex", "online": True}) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_bool_get.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_bool_get(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_int_get.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_int_get(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(5) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345")
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/publish/publish_encrypted_string_get.yaml',
        filter_query_parameters=['uuid', 'pnsdk']
    )
    def test_publish_encrypted_string_get(self, crypto_mock):
        try:
            env = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message("encrypted string") \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="spamspamspam1234")
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/publish/publish_encrypted_list_get.yaml',
        filter_query_parameters=['uuid', 'pnsdk']
    )
    def test_publish_encrypted_list_get(self, crypto_mock):
        try:
            env = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message(["encrypted", "list"]) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_string_post.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_string_post(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message("hi") \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_list_post.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_list_post(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(["hi", "hi2", "hi3"]) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_object_post.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
                         match_on=['method', 'scheme', 'host', 'port', 'path', 'query', 'object_in_body'])
    def test_publish_object_post(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message({"name": "Alex", "online": True}) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_bool_post.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_bool_post(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(True) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_int_post.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_int_post(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(5) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_encrypted_string_post.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_encrypted_string_post(self):
        try:
            env = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message("encrypted string POST") \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_encrypted_list_post.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_encrypted_list_post(self):
        try:
            env = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message(["encrypted", "list", "POST"]) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/invalid_key.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_invalid_key(self):
        config = pnconf_demo_copy()
        config.publish_key = "fake"

        try:
            PubNub(config).publish() \
                .channel("ch1") \
                .message("hey") \
                .sync()

            self.fail(Exception("Should throw exception", 'pnsdk'))
        except PubNubException as e:
            assert "Invalid Key" in str(e)

    def test_missing_message_error(self):
        try:
            PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(None) \
                .sync()

            self.fail(Exception("Should throw exception"))
        except PubNubException as e:
            assert "Message missing" in str(e)

    def test_missing_channel_error(self):
        try:
            PubNub(pnconf).publish() \
                .channel("") \
                .message("hey") \
                .sync()

            self.fail(Exception("Should throw exception"))
        except PubNubException as e:
            assert "Channel missing" in str(e)

    def test_non_serializable_error(self):
        def func():
            pass

        try:
            PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(func) \
                .sync()

            self.fail(Exception("Should throw exception"))
        except PubNubException as e:
            assert "not JSON serializable" in str(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_with_meta.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'], match_on=['meta_object_in_query'])
    def test_publish_with_meta(self):
        meta = {'a': 2, 'b': 'qwer'}

        try:
            env = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message("hey") \
                .meta(meta) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="killerrabbit1234")
    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/publish/publish_do_not_store.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub']
    )
    def test_publish_do_not_store(self, crypto_mock):
        try:
            env = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message("hey") \
                .should_store(False) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/publish/publish_with_ptto_and_replicate.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub']
    )
    def test_publish_with_ptto_and_replicate(self):
        timetoken_to_override = 16057799474000000

        env = PubNub(pnconf_file_copy()).publish()\
            .channel("ch1")\
            .message("hi")\
            .replicate(False)\
            .ptto(timetoken_to_override)\
            .sync()

        assert isinstance(env.result, PNPublishResult)
        # note: for requests url is string, for httpx is object
        if hasattr(env.status.client_request.url, 'query'):
            query = urllib.parse.parse_qs(env.status.client_request.url.query.decode())
        else:
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(env.status.client_request.url).query)
        assert "ptto" in query
        assert "norep" in query

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/publish/publish_with_single_quote_message.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub']
    )
    def test_single_quote_character_message_encoded_ok(self):
        envelope = PubNub(pnconf).publish()\
            .channel("ch1")\
            .message('"')\
            .sync()

        assert envelope

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_ttl_0.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_ttl_0(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message("hi") \
                .ttl(0) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_ttl_100.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_ttl_100(self):
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message("hi") \
                .ttl(100) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_custom_message_type(self):
        with pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_custom_message_type.json',
                                 filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json') as cassette:
            envelope = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message("hi") \
                .custom_message_type('test_message') \
                .sync()

            assert isinstance(envelope.result, PNPublishResult)
            assert envelope.result.timetoken > 1
            assert len(cassette) == 1
            uri = urllib.parse.urlparse(cassette.requests[0].uri)
            query = urllib.parse.parse_qs(uri.query)
            assert 'custom_message_type' in query.keys()
            assert query['custom_message_type'] == ['test_message']
