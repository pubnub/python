import logging
import threading
import unittest
import pubnub
from pubnub.enums import PNStatusCategory

from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from tests.helper import pnconf, pnconf_enc, pnconf_pam_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubSuccessPublish(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

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

    def assert_success_publish_get(self, msg):
        PubNub(pnconf).publish() \
            .channel("ch1") \
            .message(msg) \
            .pn_async(self.callback)

        self.assert_success()

    def assert_success_publish_post(self, msg):
        PubNub(pnconf).publish() \
            .channel("ch1") \
            .message(msg) \
            .use_post(True) \
            .pn_async(self.callback)

        self.assert_success()

    def test_publish_get(self):
        self.assert_success_publish_get("hi")
        self.assert_success_publish_get(5)
        self.assert_success_publish_get(True)
        self.assert_success_publish_get(["hi", "hi2", "hi3"])
        self.assert_success_publish_get({"name": "Alex", "online": True})

    def test_publish_post(self):
        self.assert_success_publish_post("hi")
        self.assert_success_publish_post(5)
        self.assert_success_publish_post(True)
        self.assert_success_publish_post(["hi", "hi2", "hi3"])
        self.assert_success_publish_post({"name": "Alex", "online": True})

    def test_publish_encrypted_list_get(self):
        pubnub = PubNub(pnconf_enc)

        pubnub.publish() \
            .channel("ch1") \
            .message(["encrypted", "list"]) \
            .pn_async(self.callback)

        self.assert_success()

    def test_publish_encrypted_string_get(self):
        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message("encrypted string") \
            .pn_async(self.callback)

        self.assert_success()

    def test_publish_encrypted_list_post(self):
        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message(["encrypted", "list"]) \
            .use_post(True) \
            .pn_async(self.callback)

        self.assert_success()

    def test_publish_encrypted_string_post(self):
        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message("encrypted string") \
            .use_post(True) \
            .pn_async(self.callback)

        self.assert_success()

    def test_publish_with_meta(self):
        meta = {'a': 2, 'b': 'qwer'}

        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message("hey") \
            .meta(meta) \
            .pn_async(self.callback)

        self.assert_success()

    def test_publish_do_not_store(self):
        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message("hey") \
            .should_store(False) \
            .pn_async(self.callback)

        self.assert_success()


class TestPubNubErrorPublish(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def test_invalid_key(self):
        self.invalid_key_message = ""
        config = PNConfiguration()
        config.publish_key = "fake"
        config.subscribe_key = "demo"
        config.enable_subscribe = False

        PubNub(config).publish() \
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
        PubNub(pnconf).publish() \
            .channel("ch1") \
            .message(None) \
            .pn_async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.response is None
        assert "Message missing" in str(self.status.error_data.exception)

    def test_missing_chanel(self):
        PubNub(pnconf).publish() \
            .channel("") \
            .message("hey") \
            .pn_async(self.callback)

        assert self.status.is_error()
        assert self.response is None
        assert "Channel missing" in str(self.status.error_data.exception)

    def test_non_serializable(self):
        def method():
            pass

        PubNub(pnconf).publish() \
            .channel("ch1") \
            .message(method) \
            .pn_async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.response is None
        assert "not JSON serializable" in str(self.status.error_data.exception)

    def test_not_permitted(self):
        pnconf = pnconf_pam_copy()
        pnconf.secret_key = None

        PubNub(pnconf).publish() \
            .channel("not_permitted_channel") \
            .message("correct message") \
            .pn_async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.response is None
        assert "HTTP Client Error (403)" in str(self.status.error_data.exception)
        assert "Forbidden" in str(self.status.error_data.exception)
        assert "Access Manager" in str(self.status.error_data.exception)
