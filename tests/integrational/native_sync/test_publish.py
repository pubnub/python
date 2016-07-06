import logging
import unittest
import pubnub

from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from tests.helper import pnconf, pnconf_enc

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubPublish(unittest.TestCase):
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
        config.enable_subscribe = False

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
