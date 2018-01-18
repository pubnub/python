import tornado
from tornado import gen
from tornado.testing import AsyncTestCase

from pubnub.pubnub_tornado import PubNubTornado, SubscribeListener
from tests.helper import pnconf_sub_copy
from tests.integrational.tornado.tornado_helper import connect_to_channel, disconnect_from_channel
from tests.integrational.tornado.vcr_tornado_decorator import use_cassette_and_stub_time_sleep


class TestPubNubAsyncWhereNow(AsyncTestCase):
    def setUp(self):
        super(TestPubNubAsyncWhereNow, self).setUp()
        self.pubnub = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/where_now/single_channel.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pres'])
    @tornado.testing.gen_test(timeout=15)
    def test_where_now_single_channel(self):
        ch = "where-now-tornado-ch"
        uuid = "where-now-tornado-uuid"
        self.pubnub.config.uuid = uuid

        yield connect_to_channel(self.pubnub, ch)
        yield gen.sleep(10)
        env = yield self.pubnub.where_now() \
            .uuid(uuid) \
            .future()

        channels = env.result.channels

        assert len(channels) == 1
        assert channels[0] == ch

        yield disconnect_from_channel(self.pubnub, ch)
        self.pubnub.stop()
        self.stop()

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/where_now/multiple_channels.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pres'])
    @tornado.testing.gen_test(timeout=15)
    def test_multiple_channels(self):
        ch1 = "where-now-tornado-ch1"
        ch2 = "where-now-tornado-ch2"
        uuid = "where-now-tornado-uuid"
        self.pubnub.config.uuid = uuid

        callback_messages = SubscribeListener()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channels(ch1).execute()
        yield callback_messages.wait_for_connect()

        self.pubnub.subscribe().channels(ch2).execute()
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
