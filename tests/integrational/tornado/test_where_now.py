import tornado
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase

from pubnub.pubnub_tornado import PubNubTornado
from tests import helper
from tests.helper import pnconf_sub_copy
from tests.integrational.tornado.tornado_helper import connect_to_channel, disconnect_from_channel


class TestPubNubAsyncWhereNow(AsyncTestCase):
    def setUp(self):
        super(TestPubNubAsyncWhereNow, self).setUp()
        self.pubnub = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)

    @tornado.testing.gen_test(timeout=15)
    def test_single_channel(self):
        ch = helper.gen_channel("wherenow-asyncio-channel")
        uuid = helper.gen_channel("wherenow-asyncio-uuid")
        self.pubnub.config.uuid = uuid

        yield connect_to_channel(self.pubnub, ch)
        yield gen.sleep(7)
        env = yield self.pubnub.where_now() \
            .uuid(uuid) \
            .future()

        channels = env.result.channels

        assert len(channels) == 1
        assert channels[0] == ch

        yield disconnect_from_channel(self.pubnub, ch)
        self.pubnub.stop()
        self.stop()

    @tornado.testing.gen_test(timeout=15)
    def test_multiple_channels(self):
        ch1 = helper.gen_channel("here-now")
        ch2 = helper.gen_channel("here-now")
        uuid = helper.gen_channel("wherenow-asyncio-uuid")
        self.pubnub.config.uuid = uuid

        yield connect_to_channel(self.pubnub, [ch1, ch2])
        yield gen.sleep(5)
        env = yield self.pubnub.where_now() \
            .uuid(uuid) \
            .future()

        channels = env.result.channels

        assert len(channels) == 2
        assert ch1 in channels
        assert ch2 in channels

        yield disconnect_from_channel(self.pubnub, [ch1, ch2])
        self.pubnub.stop()
        self.stop()
