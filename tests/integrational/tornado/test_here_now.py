import tornado
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase

from pubnub.pubnub_tornado import PubNubTornado
from tests import helper
from tests.helper import pnconf
from tests.integrational.tornado.tornado_helper import connect_to_channel, disconnect_from_channel


class TestPubNubAsyncHereNow(AsyncTestCase):
    def setUp(self):
        super(TestPubNubAsyncHereNow, self).setUp()
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

    @tornado.testing.gen_test
    def test_single_channel(self):
        ch = helper.gen_channel("herenow-unit")
        yield connect_to_channel(self.pubnub, ch)
        yield gen.sleep(2)
        env = yield self.pubnub.here_now() \
            .channels(ch) \
            .include_uuids(True) \
            .future()

        assert env.result.total_channels == 1
        assert env.result.total_occupancy >= 1

        channels = env.result.channels

        assert len(channels) == 1
        assert channels[0].occupancy == 1
        assert channels[0].occupants[0].uuid == self.pubnub.uuid

        yield disconnect_from_channel(self.pubnub, ch)
        self.pubnub.stop()
        self.stop()

    @tornado.testing.gen_test(timeout=10)
    def test_multiple_channels(self):
        ch1 = helper.gen_channel("here-now")
        ch2 = helper.gen_channel("here-now")
        yield connect_to_channel(self.pubnub, [ch1, ch2])
        yield gen.sleep(4)
        env = yield self.pubnub.here_now() \
            .channels([ch1, ch2]) \
            .future()

        assert env.result.total_channels == 2
        assert env.result.total_occupancy >= 1

        channels = env.result.channels

        assert len(channels) == 2
        assert channels[0].occupancy == 1
        assert channels[0].occupants[0].uuid == self.pubnub.uuid
        assert channels[1].occupancy == 1
        assert channels[1].occupants[0].uuid == self.pubnub.uuid

        yield disconnect_from_channel(self.pubnub, [ch1, ch2])
        self.pubnub.stop()
        self.stop()

    @tornado.testing.gen_test
    def test_global(self):
        ch1 = helper.gen_channel("here-now")
        ch2 = helper.gen_channel("here-now")

        yield connect_to_channel(self.pubnub, [ch1, ch2])
        yield gen.sleep(2)

        env = yield self.pubnub.here_now().future()

        assert env.result.total_channels >= 2
        assert env.result.total_occupancy >= 1

        yield disconnect_from_channel(self.pubnub, [ch1, ch2])

        self.pubnub.stop()
        self.stop()
