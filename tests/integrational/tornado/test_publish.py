from tornado.testing import AsyncTestCase

from pubnub.models.consumer.pubsub import PNPublishResult

from pubnub.pubnub_tornado import PubNubTornado
from tests.helper import pnconf, pnconf_enc

channel = "tornado-int-publish"


class TestPubNubAsyncPublish(AsyncTestCase):
    def assert_success(self, pub):
        self.pubnub.set_ioloop(self.io_loop)

        def success(res):
            self.pubnub.stop()
            self.stop()
            assert isinstance(res, PNPublishResult)
            assert res.timetoken > 0
            assert len(res.original_response) > 0

        def error(err):
            self.pubnub.stop()
            self.stop()
            self.fail("Error while success is expected: " + str(err))

        pub.async(success, error)

        self.pubnub.start()
        self.wait()

    def assert_success_publish_get(self, msg):
        self.pubnub = PubNubTornado(pnconf)
        self.assert_success(self.pubnub.publish().channel("my_channel").message(msg))

    def assert_success_publish_post(self, msg):
        self.pubnub = PubNubTornado(pnconf)
        self.assert_success(self.pubnub.publish().channel("my_channel").message(msg).use_post(True))

    def assert_success_publish_get_encrypted(self, msg):
        self.pubnub = PubNubTornado(pnconf_enc)
        self.assert_success(self.pubnub.publish().channel("my_channel").message(msg))

    def assert_success_publish_post_encrypted(self, msg):
        self.pubnub = PubNubTornado(pnconf_enc)
        self.assert_success(self.pubnub.publish().channel("my_channel").message(msg).use_post(True))

    def assert_error(self, pub):
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

        pub.async(success, error)

        pubnub.start()
        self.wait()

    def test_publish_string_via_get(self):
        self.assert_success_publish_get("hi")
        self.assert_success_publish_get(5)
        self.assert_success_publish_get(True)
        self.assert_success_publish_get(["hi", "hi2", "hi3"])
        self.assert_success_publish_get({"name": "Alex", "online": True})

    def test_publish_string_via_post(self):
        self.assert_success_publish_post("hi")
        self.assert_success_publish_post(5)
        self.assert_success_publish_post(True)
        self.assert_success_publish_post(["hi", "hi2", "hi3"])
        self.assert_success_publish_post({"name": "Alex", "online": True})

    def test_publish_string_via_get_encrypted(self):
        self.assert_success_publish_get_encrypted("hi")
        self.assert_success_publish_get_encrypted(5)
        self.assert_success_publish_get_encrypted(True)
        self.assert_success_publish_get_encrypted(["hi", "hi2", "hi3"])
        self.assert_success_publish_get_encrypted({"name": "Alex", "online": True})

    def test_publish_string_via_post_encrypted(self):
        self.assert_success_publish_post_encrypted("hi")
        self.assert_success_publish_post_encrypted(5)
        self.assert_success_publish_post_encrypted(True)
        self.assert_success_publish_post_encrypted(["hi", "hi2", "hi3"])
        self.assert_success_publish_post_encrypted({"name": "Alex", "online": True})

