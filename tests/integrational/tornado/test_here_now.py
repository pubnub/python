import tornado
from tornado import gen
from tornado.locks import Event
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase

from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub_tornado import PubNubTornado
from tests import helper
from tests.helper import pnconf


class ConnectionEvent(SubscribeCallback):
    def __init__(self, event, expected_status_checker):
        self.event = event
        self.expected_status_checker = expected_status_checker

    def status(self, pubnub, status):
        if self.expected_status_checker(status):
            self.event.set()

    def presence(self, pubnub, presence):
        pass

    def message(self, pubnub, message):
        pass


@tornado.gen.coroutine
def connect_to_channel(pubnub, channel):
    event = Event()
    callback = ConnectionEvent(event, helper.is_subscribed_event)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels(channel).execute()
    yield event.wait()


@tornado.gen.coroutine
def disconnect_from_channel(pubnub, channel):
    event = Event()
    callback = ConnectionEvent(event, helper.is_unsubscribed_event)
    pubnub.add_listener(callback)
    pubnub.unsubscribe().channels(channel).execute()
    yield event.wait()


class TestPubNubAsyncHereNow(AsyncTestCase):
    def setUp(self):
        super(TestPubNubAsyncHereNow, self).setUp()
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

    @tornado.testing.gen_test
    def test_success(self):
        ch1 = helper.gen_channel("here-now")
        ch2 = helper.gen_channel("here-now")
        yield connect_to_channel(self.pubnub, [ch1, ch2])
        yield gen.sleep(2)
        env = yield self.pubnub.here_now() \
            .channels([ch1, ch2]) \
            .include_state(False) \
            .future()

        print(env.result)
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

