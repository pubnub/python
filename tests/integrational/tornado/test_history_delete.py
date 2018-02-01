
from tornado.testing import AsyncTestCase
from pubnub.pubnub_tornado import PubNubTornado
from tests.helper import pnconf


class TestPubNubAsyncPublish(AsyncTestCase):  # pylint: disable=W0612
    def setUp(self):
        AsyncTestCase.setUp(self)
        self.env = None

    def callback(self, tornado_res):
        self.env = tornado_res.result()
        self.pubnub.stop()
        self.stop()

    def assert_success(self, pub):
        pub.future().add_done_callback(self.callback)

        self.pubnub.start()
        self.wait()

        if self.env.status.error:
            raise AssertionError()

    def test_success(self):
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)
        self.assert_success(self.pubnub.delete_messages().channel("my-ch").start(123).end(456))

    def test_super_call(self):
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)
        self.assert_success(self.pubnub.delete_messages().channel("my-ch- |.* $").start(123).end(456))
