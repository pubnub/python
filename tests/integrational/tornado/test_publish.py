from tornado.testing import AsyncTestCase

from pubnub.models.consumer.pubsub import PNPublishResult

from pubnub.pubnub_tornado import PubNubTornado
from tests.helper import pnconf


class TestPubNubAsyncPublish(AsyncTestCase):
    def test_publish_string_via_get(self):
        pubnub = PubNubTornado(pnconf)
        pubnub.set_ioloop(self.io_loop)

        def success(res):
            pubnub.stop()
            self.stop()
            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 0
            assert len(res.original_response) > 0

        def error(err):
            pubnub.stop()
            self.stop()
            self.fail("Error while success is expected: " + str(err))

        pubnub.publish() \
            .channel("my_channel") \
            .message("async hello string using GET") \
            .async(success, error)

        pubnub.start()
        self.wait()

    def test_publish_list_via_get(self):
        pubnub = PubNubTornado(pnconf)
        pubnub.set_ioloop(self.io_loop)

        def success(res):
            pubnub.stop()
            self.stop()
            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 0
            assert len(res.original_response) > 0

        def error(err):
            pubnub.stop()
            self.stop()
            self.fail("Error while success is expected: " + str(err))

        pubnub.publish() \
            .channel("my_channel") \
            .message(["async", "hello", "list", "using GET"]) \
            .async(success, error)

        pubnub.start()
        self.wait()

    def test_publish_string_via_post(self):
        pubnub = PubNubTornado(pnconf)
        pubnub.set_ioloop(self.io_loop)

        def success(res):
            pubnub.stop()
            self.stop()
            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 0
            assert len(res.original_response) > 0

        def error(err):
            pubnub.stop()
            self.stop()
            self.fail("Error while success is expected: " + str(err))

        pubnub.publish() \
            .channel("my_channel") \
            .message("async hello string using POST") \
            .use_post(True) \
            .async(success, error)

        pubnub.start()
        self.wait()

    def test_publish_list_via_post(self):
        pubnub = PubNubTornado(pnconf)
        pubnub.set_ioloop(self.io_loop)

        def success(res):
            pubnub.stop()
            self.stop()
            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 0
            assert len(res.original_response) > 0

        def error(err):
            pubnub.stop()
            self.stop()
            self.fail("Error while success is expected: " + str(err))

        pubnub.publish() \
            .channel("my_channel") \
            .message(["async", "hello", "list", "using POST"]) \
            .use_post(True) \
            .async(success, error)

        pubnub.start()
        self.wait()
