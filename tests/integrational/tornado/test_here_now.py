from tornado.testing import AsyncHTTPTestCase, AsyncTestCase

from pubnub.pnconfiguration import PNConfiguration

from pubnub.pubnub_tornado import PubNubTornado


class TestPubNubAsyncAsyncHereNow(AsyncTestCase):

    def test_success(self):
        pnconf = PNConfiguration()
        pubnub = PubNubTornado(pnconf)
        pubnub.set_ioloop(self.io_loop)

        def success(res):
            print(res.total_occupancy)
            pubnub.stop()
            self.stop()

        def error(err):
            print(err)
            pubnub.stop()
            self.stop()

        pubnub.here_now() \
            .channels(["ch1", "ch2", "ch3", "demo"]) \
            .include_state(False) \
            .async(success, error)

        pubnub.start()
        self.wait()
