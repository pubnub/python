import vcr

from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from tests.helper import pnconf

import unittest

# TODO: server error handling test
# TODO: arguments error handling test
# TODO: post method test
# TODO: meta argument method test


class TestPubNubSyncPublish(unittest.TestCase):
    @vcr.use_cassette('integrational/fixtures/publish/sync_success.yaml',
                      filter_query_parameters=['uuid'])
    def test_success(self):
        pubnub = PubNub(pnconf)

        try:
            res = pubnub.publish() \
                .channel("ch1") \
                .message("hi") \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    @vcr.use_cassette('integrational/fixtures/publish/sync_success_list.yaml',
                      filter_query_parameters=['uuid'])
    def test_success_list(self):
        pubnub = PubNub(pnconf)

        try:
            res = pubnub.publish() \
                .channel("ch1") \
                .message(["hi", "hi2", "hi3"]) \
                .sync()

            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1
        except PubNubException as e:
            self.fail(e)

    def test_server_error(self):
        # TODO: should throw error
        config = PNConfiguration()
        config.publish_key = "demo"
        config.subscribe_key = "demos"
        pubnub = PubNub(config)

        try:
            pubnub.publish() \
                .channel("ch1") \
                .message("hey") \
                .sync()

            self.fail(Exception("Should throw exception"))
        except PubNubException as e:
            assert e is not None


class TestPubNubAsyncPublish(unittest.TestCase):
    @vcr.use_cassette('integrational/fixtures/publish/async_success.yaml',
                      filter_query_parameters=['uuid'])
    def test_success(self):
        pubnub = PubNub(pnconf)

        def success(res):
            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1

        def error(e):
            self.fail(e)

        thread = pubnub.publish() \
            .channel("ch1") \
            .message("hi") \
            .async(success, error)

        thread.join()

    @vcr.use_cassette('integrational/fixtures/publish/async_success_list.yaml',
                      filter_query_parameters=['uuid'])
    def test_success_list(self):
        pubnub = PubNub(pnconf)

        def success(res):
            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 1

        def error(e):
            self.fail(e)

        thread = pubnub.publish() \
            .channel("ch1") \
            .message(["hi", "hi2", "hi3"]) \
            .async(success, error)

        thread.join()
