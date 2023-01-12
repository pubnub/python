import logging
import unittest

import pubnub
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf, pnconf_env, pnconf_enc_env, pnconf_demo_copy, pnconf_file_copy
from tests.integrational.vcr_helper import pn_vcr
from unittest.mock import patch

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubPublish(unittest.TestCase):
    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_string_get.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_string_get(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message("hi") \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_list_get.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_list_get(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message(["hi", "hi2", "hi3"]) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_object_get.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json',
                         match_on=['method', 'scheme', 'host', 'port', 'object_in_path', 'query'])
    def test_publish_object_get(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message({"name": "Alex", "online": True}) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_bool_get.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_bool_get(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_int_get.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_int_get(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message(5) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345")
    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_encrypted_string_get.json',
                        filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_encrypted_string_get(self, crypto_mock):
        try:
            env = PubNub(pnconf_enc_env).publish() \
                .channel("ch1") \
                .message("encrypted string") \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="spamspamspam1234")
    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_encrypted_list_get.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_encrypted_list_get(self, crypto_mock):
        try:
            env = PubNub(pnconf_enc_env).publish() \
                .channel("ch1") \
                .message(["encrypted", "list"]) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_string_post.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_string_post(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message("hi") \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_list_post.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_list_post(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message(["hi", "hi2", "hi3"]) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_object_post.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json',
                         match_on=['method', 'scheme', 'host', 'port', 'path', 'query', 'object_in_body'])
    def test_publish_object_post(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message({"name": "Alex", "online": True}) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_bool_post.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_bool_post(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message(True) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_int_post.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_int_post(self):
        try:
            env = PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message(5) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_encrypted_string_post.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_encrypted_string_post(self):
        try:
            env = PubNub(pnconf_enc_env).publish() \
                .channel("ch1") \
                .message("encrypted string POST") \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_encrypted_list_post.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_publish_encrypted_list_post(self):
        try:
            env = PubNub(pnconf_enc_env).publish() \
                .channel("ch1") \
                .message(["encrypted", "list", "POST"]) \
                .use_post(True) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/invalid_key.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
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
            PubNub(pnconf_env).publish() \
                .channel("ch1") \
                .message(None) \
                .sync()

            self.fail(Exception("Should throw exception"))
        except PubNubException as e:
            assert "Message missing" in str(e)

    def test_missing_channel_error(self):
        try:
            PubNub(pnconf_env).publish() \
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

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_with_meta.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json',
                         match_on=['meta_object_in_query'])
    def test_publish_with_meta(self):
        meta = {'a': 2, 'b': 'qwer'}

        try:
            env = PubNub(pnconf_enc_env).publish() \
                .channel("ch1") \
                .message("hey") \
                .meta(meta) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="killerrabbit1234")
    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_do_not_store.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_pub'], serializer='pn_json')
    def test_publish_do_not_store(self, crypto_mock):
        try:
            env = PubNub(pnconf_enc_env).publish() \
                .channel("ch1") \
                .message("hey") \
                .should_store(False) \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_with_ptto_and_replicate.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_pub'], serializer='pn_json')
    def test_publish_with_ptto_and_replicate(self):
        timetoken_to_override = 16057799474000000

        env = PubNub(pnconf_env).publish()\
            .channel("ch1")\
            .message("hi")\
            .replicate(False)\
            .ptto(timetoken_to_override)\
            .sync()

        assert isinstance(env.result, PNPublishResult)
        assert "ptto" in env.status.client_request.url
        assert "norep" in env.status.client_request.url

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/publish_with_single_quote_message.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_pub'], serializer='pn_json')
    def test_single_quote_character_message_encoded_ok(self):
        envelope = PubNub(pnconf_env).publish()\
            .channel("ch1")\
            .message('"')\
            .sync()

        assert envelope
