import logging
import threading
import unittest

import time

import pubnub
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from tests.helper import pnconf, pnconf_enc

# import pydevd as pydevd
pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubSyncPublish(unittest.TestCase):
    # @vcr.use_cassette('integrational/fixtures/publish/publish_string_get.yaml',
    #                   filter_query_parameters=['uuid'])
    def test_publish_string_get(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message("hi") \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    # @vcr.use_cassette('integrational/fixtures/publish/publish_list_get.yaml',
    #                   filter_query_parameters=['uuid'])
    def test_publish_list_get(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(["hi", "hi2", "hi3"]) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_object_get(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message({"name": "Alex", "online": True}) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_bool_get(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(True) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_int_get(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(5) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_encrypted_string_get(self):
        try:
            res = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message("encrypted string") \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_encrypted_list_get(self):
        try:
            res = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message(["encrypted", "list"]) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    # @vcr.use_cassette('integrational/fixtures/publish/publish_string_post.yaml',
    #                   filter_query_parameters=['uuid'])
    def test_publish_string_post(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message("hi") \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    # @vcr.use_cassette('integrational/fixtures/publish/publish_list_post.yaml',
    #                   filter_query_parameters=['uuid'])
    def test_publish_list_post(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(["hi", "hi2", "hi3"]) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_object_post(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message({"name": "Alex", "online": True}) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_bool_post(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(True) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_int_post(self):
        try:
            res = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message(5) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_encrypted_string_post(self):
        try:
            res = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message("encrypted string POST") \
                .use_post(True) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_encrypted_list_post(self):
        try:
            res = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message(["encrypted", "list", "POST"]) \
                .use_post(True) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_invalid_key(self):
        config = PNConfiguration()
        config.publish_key = "fake"
        config.subscribe_key = "demo"

        try:
            PubNub(config).publish() \
                .channel("ch1") \
                .message("hey") \
                .sync()

            self.fail(Exception("Should throw exception"))
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

    def test_publish_with_meta(self):
        meta = {'a': 2, 'b': 'qwer'}

        try:
            res = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message("hey") \
                .meta(meta) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_publish_do_not_store(self):
        try:
            res = PubNub(pnconf_enc).publish() \
                .channel("ch1") \
                .message("hey") \
                .should_store(False) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)


class TestPubNubAsyncSuccessPublish(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def assert_success(self):
        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNPublishResult)
        assert self.response.timetoken > 1

    def assert_success_publish_get(self, msg):
        PubNub(pnconf).publish() \
            .channel("ch1") \
            .message(msg) \
            .async(self.callback)

        self.assert_success()

    def assert_success_publish_post(self, msg):
        PubNub(pnconf).publish() \
            .channel("ch1") \
            .message(msg) \
            .use_post(True) \
            .async(self.callback)

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
            .async(self.callback)

        self.assert_success()
        pubnub.stop()

    def test_publish_encrypted_string_get(self):
        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message("encrypted string") \
            .async(self.callback)

        self.assert_success()

    def test_publish_encrypted_list_post(self):
        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message(["encrypted", "list"]) \
            .use_post(True) \
            .async(self.callback)

        self.assert_success()

    def test_publish_encrypted_string_post(self):
        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message("encrypted string") \
            .use_post(True) \
            .async(self.callback)

        self.assert_success()

    def test_publish_with_meta(self):
        meta = {'a': 2, 'b': 'qwer'}

        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message("hey") \
            .meta(meta) \
            .async(self.callback)

        self.assert_success()

    def test_publish_do_not_store(self):
        PubNub(pnconf_enc).publish() \
            .channel("ch1") \
            .message("hey") \
            .should_store(False) \
            .async(self.callback)

        self.assert_success()


class TestPubNubAsyncErrorPublish(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def test_invalid_k(self):
        self.invalid_key_message = ""
        config = PNConfiguration()
        config.publish_key = "fake"
        config.subscribe_key = "demo"

        PubNub(config).publish() \
            .channel("ch1") \
            .message("hey") \
            .async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.response.envelope[0] is 0
        assert self.response.envelope[1] == 'Invalid Key'
        assert "HTTP Client Error (400):" in str(self.status.error_data.exception)
        assert "Invalid Key" in str(self.status.error_data.exception)

    def test_missing_message(self):
        PubNub(pnconf).publish() \
            .channel("ch1") \
            .message(None) \
            .async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.response is None
        assert "Message missing" in str(self.status.error_data.exception)

    def test_missing_chanel(self):
        PubNub(pnconf).publish() \
            .channel("") \
            .message("hey") \
            .async(self.callback)

        assert self.status.is_error()
        assert self.response is None
        assert "Channel missing" in str(self.status.error_data.exception)

    def test_non_serializable(self):
        def method():
            pass

        PubNub(pnconf).publish() \
            .channel("ch1") \
            .message(method) \
            .async(self.callback)

        self.event.wait()

        assert self.status.is_error()
        assert self.response is None
        assert "not JSON serializable" in str(self.status.error_data.exception)
