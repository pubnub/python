import logging

import tornado
import tornado.gen
from tornado import gen
from tornado.testing import AsyncTestCase

import pubnub as pn
from pubnub.pubnub_tornado import PubNubTornado, SubscribeListener
from tests.helper import pnconf_sub_copy
from tests.integrational.tornado.tornado_helper import connect_to_channel, disconnect_from_channel
from tests.integrational.tornado.vcr_tornado_decorator import use_cassette_and_stub_time_sleep

pn.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubAsyncHereNow(AsyncTestCase):
    def setUp(self):
        super(TestPubNubAsyncHereNow, self).setUp()
        self.pubnub = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/here_now/single.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pres'])
    @tornado.testing.gen_test(timeout=15)
    def test_here_now_single_channel(self):
        ch = 'test-here-now-channel'
        self.pubnub.config.uuid = 'test-here-now-uuid'
        yield connect_to_channel(self.pubnub, ch)
        yield tornado.gen.sleep(10)
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

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/here_now/multiple.yaml',
        filter_query_parameters=['uuid', 'tt', 'tr', 'pnsdk', 'l_pres'])
    @tornado.testing.gen_test(timeout=120)
    def test_here_now_multiple_channels(self):
        ch1 = 'test-here-now-channel1'
        ch2 = 'test-here-now-channel2'
        self.pubnub.config.uuid = 'test-here-now-uuid'
        # print("connecting to the first...")
        yield connect_to_channel(self.pubnub, ch1)
        # print("...connected to the first")
        yield gen.sleep(1)
        # print("connecting to the second...")
        self.pubnub.subscribe().channels(ch2).execute()
        # print("...connected to the second")
        yield gen.sleep(5)
        env = yield self.pubnub.here_now() \
            .channels([ch1, ch2]) \
            .future()

        assert env.result.total_channels == 2
        assert env.result.total_occupancy >= 1

        channels = env.result.channels

        assert len(channels) == 2
        assert channels[0].occupancy >= 1
        assert channels[0].occupants[0].uuid == self.pubnub.uuid
        assert channels[1].occupancy >= 1
        assert channels[1].occupants[0].uuid == self.pubnub.uuid

        yield disconnect_from_channel(self.pubnub, [ch1, ch2])
        self.pubnub.stop()
        self.stop()

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/here_now/global.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pres'])
    @tornado.testing.gen_test(timeout=15)
    def test_here_now_global(self):
        ch1 = 'test-here-now-channel1'
        ch2 = 'test-here-now-channel2'
        self.pubnub.config.uuid = 'test-here-now-uuid'

        callback_messages = SubscribeListener()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channels(ch1).execute()
        yield callback_messages.wait_for_connect()

        self.pubnub.subscribe().channels(ch2).execute()
        yield gen.sleep(6)

        env = yield self.pubnub.here_now().future()

        assert env.result.total_channels >= 2
        assert env.result.total_occupancy >= 1

        yield disconnect_from_channel(self.pubnub, [ch1, ch2])

        self.pubnub.stop()
        self.stop()
