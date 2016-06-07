import tornado
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase
from pubnub.pubnub_tornado import PubNubTornado
from tests.helper import pnconf


class TestPubNubAsyncHereNow(AsyncTestCase):
    @tornado.testing.gen_test
    def test_success(self):
        pubnub = PubNubTornado(pnconf)
        pubnub.set_ioloop(self.io_loop)

        env = yield pubnub.here_now() \
            .channels(["ch1", "ch2", "ch3", "demo"]) \
            .include_state(False) \
            .future()

        print(env.result)

        pubnub.stop()
        self.stop()

