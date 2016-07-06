import tornado
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase
from pubnub.pubnub_tornado import PubNubTornado
from tests import helper
from tests.helper import pnconf

# TODO: test for 'No valid channels specified'
# TODO: test for CG state getter (after implementation of CG methods)


class TestPubNubState(AsyncTestCase):
    def setUp(self):
        super(TestPubNubState, self).setUp()
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

    @tornado.testing.gen_test
    def test_single_channel(self):
        ch = helper.gen_channel("herenow-unit")
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

    @tornado.testing.gen_test
    def test_multiple_channels(self):
        ch1 = helper.gen_channel("herenow-unit")
        ch2 = helper.gen_channel("herenow-unit")
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
