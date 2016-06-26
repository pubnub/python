import logging
import pubnub as pn

from tornado.testing import AsyncTestCase
from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub_tornado import PubNubTornado
from tests import helper
from tests.helper import pnconf_copy

pn.set_stream_logger('pubnub', logging.DEBUG)

ch1 = "ch1"
ch2 = "ch2"


class SubscriptionTest(object):
    def __init__(self):
        super(SubscriptionTest, self).__init__()
        self.pubnub = None
        self.pubnub_listener = None


class TestMultipleChannelSubscriptions(AsyncTestCase, SubscriptionTest):
    def setUp(self):
        super(TestMultipleChannelSubscriptions, self).setUp()
        self.pubnub = PubNubTornado(pnconf_copy(), custom_ioloop=self.io_loop)

    def test_do(self):
        _test = self

        class MyCallback(SubscribeCallback):
            def __init__(self):
                self.subscribe = False
                self.unsubscribe = False

            def message(self, pubnub, result):
                _test.io_loop.add_callback(_test._unsubscribe)

            def status(self, pubnub, status):
                # connect event triggers only once, but probably should be triggered once for each channel
                # TODO collect 3 subscribe
                # TODO collect 3 unsubscribe
                if helper.is_subscribed_event(status):
                    self.subscribe = True
                    _test.io_loop.add_callback(_test._publish)
                elif helper.is_unsubscribed_event(status):
                    self.unsubscribe = True
                    pubnub.stop()
                    _test.stop()

            def presence(self, pubnub, presence):
                pass

        callback = MyCallback()
        self.pubnub.add_listener(callback)
        self.pubnub.subscribe().channels("ch1").execute()
        self.pubnub.subscribe().channels("ch2").execute()
        self.pubnub.subscribe().channels("ch3").execute()

        self.wait()

    def _publish(self):
        self.pubnub.publish().channel("ch2").message("hey").future()

    def _unsubscribe(self):
        self.pubnub.unsubscribe().channels(["ch1", "ch2"]).execute()
        self.io_loop.add_callback(self._unsubscribe2)

    def _unsubscribe2(self):
        self.pubnub.unsubscribe().channels(["ch3"]).execute()

