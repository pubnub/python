from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf

import unittest
import vcr

class TestPubNubSyncPublish(unittest.TestCase):
    @vcr.use_cassette('fixtures/vcr_cassettes/synopsis.yaml')
    def test_success(self):
        pubnub = PubNub(pnconf)

        try:
            res = pubnub.publish() \
                .channel("ch1") \
                .message("hi") \
                .sync()

            self.assertIsInstance(res, PNPublishResult)
            self.assertGreater(res.timetoken, 1)
        except PubNubException as e:
            self.fail(e)

    def test_success_list(self):
        pubnub = PubNub(pnconf)

        try:
            res = pubnub.publish() \
                .channel("ch1") \
                .message(["hi", "hi2", "hi3"]) \
                .sync()

            self.assertIsInstance(res, PNPublishResult)
            self.assertGreater(res.timetoken, 1)
        except PubNubException as e:
            self.fail(e)


class TestPubNubAsyncPublish(unittest.TestCase):
    def test_success(self):
        pubnub = PubNub(pnconf)

        def success(res):
            self.assertIsInstance(res, PNPublishResult)
            self.assertGreater(res.timetoken, 1)

        def error(e):
            self.fail(e)

        thread = pubnub.publish() \
            .channel("ch1") \
            .message("hi") \
            .async(success, error)

        thread.join()

    def test_success_list(self):
        pubnub = PubNub(pnconf)

        def success(res):
            self.assertIsInstance(res, PNPublishResult)
            self.assertGreater(res.timetoken, 1)

        def error(e):
            self.fail(e)

        thread = pubnub.publish() \
            .channel("ch1") \
            .message(["hi", "hi2", "hi3"]) \
            .async(success, error)

        thread.join()
