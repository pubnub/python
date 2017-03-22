import tornado
import logging
import pubnub as pn

from tornado.testing import AsyncTestCase
from pubnub.pubnub_tornado import PubNubTornado
from tests.helper import pnconf_copy, pnconf_pam_copy
from tests.integrational.tornado.vcr_tornado_decorator import use_cassette_and_stub_time_sleep


pn.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(AsyncTestCase):
    def setUp(self):
        super(TestPubNubState, self).setUp()
        self.pubnub = PubNubTornado(pnconf_copy(), custom_ioloop=self.io_loop)

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/state/single_channel.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
        match_on=['method', 'host', 'path', 'state_object_in_query'])
    @tornado.testing.gen_test
    def test_state_single_channel(self):
        ch = "state-tornado-ch"
        self.pubnub.config.uuid = 'state-tornado-uuid'
        state = {"name": "Alex", "count": 5}

        env = yield self.pubnub.set_state() \
            .channels(ch) \
            .state(state) \
            .future()

        assert env.result.state['name'] == "Alex"
        assert env.result.state['count'] == 5

        env = yield self.pubnub.get_state() \
            .channels(ch) \
            .future()

        assert env.result.channels[ch]['name'] == "Alex"
        assert env.result.channels[ch]['count'] == 5

        self.pubnub.stop()
        self.stop()

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/state/multiple_channel.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
        match_on=['method', 'host', 'path', 'state_object_in_query'])
    @tornado.testing.gen_test
    def test_multiple_channels(self):
        ch1 = "state-tornado-ch1"
        ch2 = "state-tornado-ch2"
        self.pubnub.config.uuid = 'state-tornado-uuid'
        state = {"name": "Alex", "count": 5}

        env = yield self.pubnub.set_state() \
            .channels([ch1, ch2]) \
            .state(state) \
            .future()

        assert env.result.state['name'] == "Alex"
        assert env.result.state['count'] == 5

        env = yield self.pubnub.get_state() \
            .channels([ch1, ch2]) \
            .future()

        assert env.result.channels[ch1]['name'] == "Alex"
        assert env.result.channels[ch2]['name'] == "Alex"
        assert env.result.channels[ch1]['count'] == 5
        assert env.result.channels[ch2]['count'] == 5

        self.pubnub.stop()
        self.stop()

    @tornado.testing.gen_test
    def test_super_call(self):
        ch1 = "state-tornado-ch1"
        ch2 = "state-tornado-ch2"
        pnconf = pnconf_pam_copy()
        pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)
        pubnub.config.uuid = 'test-state-tornado-uuid-|.*$'
        state = {"name": "Alex", "count": 5}

        env = yield pubnub.set_state() \
            .channels([ch1, ch2]) \
            .state(state) \
            .future()

        assert env.result.state['name'] == "Alex"
        assert env.result.state['count'] == 5

        env = yield pubnub.get_state() \
            .channels([ch1, ch2]) \
            .future()

        assert env.result.channels[ch1]['name'] == "Alex"
        assert env.result.channels[ch2]['name'] == "Alex"
        assert env.result.channels[ch1]['count'] == 5
        assert env.result.channels[ch2]['count'] == 5

        pubnub.stop()
        self.stop()
