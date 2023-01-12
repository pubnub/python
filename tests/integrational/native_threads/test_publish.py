import logging
import threading
import unittest
import pubnub

from tests.integrational.vcr_helper import pn_vcr
from pubnub.enums import PNStatusCategory

from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf_demo_copy, pnconf_pam_env_copy, pnconf_env_copy, pnconf_enc_env_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubSuccessPublish(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()
        self.pnconf = pnconf_env_copy()
        self.pnconf_enc = pnconf_enc_env_copy()
        self.pnconf_enc.use_random_initialization_vector = False

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def assert_success(self):
        self.event.wait()
        if self.status.is_error():
            self.fail(str(self.status.error_data.exception))
        assert isinstance(self.response, PNPublishResult)
        assert self.response.timetoken > 1
        self.event.clear()
        self.response = None
        self.status = None

    def assert_success_publish(self, msg, use_post=False, config=None):
        config = self.pnconf if not config else config
        PubNub(config).publish() \
            .channel("ch1") \
            .message(msg) \
            .use_post(use_post) \
            .pn_async(self.callback)

        self.assert_success()

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/publish/publish_get.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
    def test_publish_get(self):
        self.assert_success_publish("hi")
        self.assert_success_publish(5)
        self.assert_success_publish(True)
        self.assert_success_publish(["hi", "hi2", "hi3"])
        self.assert_success_publish({"name": "Alex", "online": True})

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/publish/publish_post.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
    def test_publish_post(self):
        self.assert_success_publish("hi", use_post=True)
        self.assert_success_publish(5, use_post=True)
        self.assert_success_publish(True, use_post=True)
        self.assert_success_publish(["hi", "hi2", "hi3"], use_post=True)
        self.assert_success_publish({"name": "Alex", "online": True}, use_post=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/publish/publish_encrypted_get.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
    def test_publish_encrypted_get(self):
        self.assert_success_publish(["encrypted", "list"], config=self.pnconf_enc)
        self.assert_success_publish("encrypted string", config=self.pnconf_enc)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/publish/publish_encrypted_post.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
    def test_publish_encrypted_post(self):
        self.assert_success_publish(["encrypted", "list"], use_post=True, config=self.pnconf_enc)
        self.assert_success_publish("encrypted string", use_post=True, config=self.pnconf_enc)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/publish/publish_encrypted_with_meta.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
    def test_publish_encrypted_with_meta(self):
        meta = {'a': 2, 'b': 'qwer'}

        PubNub(self.pnconf_enc).publish() \
            .channel("ch1") \
            .message("hey") \
            .meta(meta) \
            .pn_async(self.callback)

        self.assert_success()

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/publish/publish_encrypted_do_not_store.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
    def test_publish_encrypted_do_not_store(self):
        PubNub(self.pnconf_enc).publish() \
            .channel("ch1") \
            .message("hey") \
            .should_store(False) \
            .pn_async(self.callback)

        self.assert_success()


class TestPubNubErrorPublish(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()
        self.pnconf = pnconf_env_copy()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/publish/publish_invalid_key.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
    def test_invalid_key(self):
        self.invalid_key_message = ""
        pn_fake_key_config = pnconf_demo_copy()
        pn_fake_key_config.publish_key = "fake"

        PubNub(pn_fake_key_config).publish() \
            .channel("ch1") \
            .message("hey") \
            .pn_async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.status.category is PNStatusCategory.PNBadRequestCategory
        assert self.status.original_response[0] == 0
        assert self.status.original_response[1] == 'Invalid Key'
        assert "HTTP Client Error (400):" in str(self.status.error_data.exception)
        assert "Invalid Key" in str(self.status.error_data.exception)

    def test_missing_message(self):
        PubNub(self.pnconf).publish() \
            .channel("ch1") \
            .message(None) \
            .pn_async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.response is None
        assert "Message missing" in str(self.status.error_data.exception)

    def test_missing_chanel(self):
        PubNub(self.pnconf).publish() \
            .channel("") \
            .message("hey") \
            .pn_async(self.callback)

        assert self.status.is_error()
        assert self.response is None
        assert "Channel missing" in str(self.status.error_data.exception)

    def test_non_serializable(self):
        def method():
            pass

        PubNub(self.pnconf).publish() \
            .channel("ch1") \
            .message(method) \
            .pn_async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.response is None
        assert "not JSON serializable" in str(self.status.error_data.exception)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_threads/publish/publish_not_permitted.json',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
    def test_not_permitted(self):
        pnconf = pnconf_pam_env_copy()
        pnconf.secret_key = None

        PubNub(pnconf).publish()\
            .channel("not_permitted_channel")\
            .message("correct message")\
            .pn_async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.response is None
        assert "HTTP Client Error (403)" in str(self.status.error_data.exception)
        assert "Forbidden" in str(self.status.error_data.exception)
        assert "Access Manager" in str(self.status.error_data.exception)
