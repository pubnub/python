import logging
import pubnub as pn

from tornado.testing import AsyncTestCase
from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub_tornado import PubNubTornado
from tests import helper
from tests.helper import pnconf

pn.set_stream_logger('pubnub', logging.DEBUG)

ch1 = "ch1"
ch2 = "ch2"


class SubscriptionTest(object):
    def __init__(self):
        super(SubscriptionTest, self).__init__()
        self.pubnub = None

# Heartbeat test steps:
# - set hb timeout to 10
# - connect to :ch-pnpres
# - connect to :ch
# - assert join event
# - block hb requests
# - assert disconnect on 11 second


class TestSubscribeUnsubscribe(AsyncTestCase, SubscriptionTest):
    def setUp(self):
        super(TestSubscribeUnsubscribe, self).setUp()
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

    def test_do(self):
        _test = self

        class MyCallback(SubscribeCallback):
            def message(self, pubnub, result):
                pass

            def status(self, pubnub, status):
                if helper.is_subscribed_event(status):
                    _test.io_loop.add_callback(_test._unsubscribe)
                elif helper.is_unsubscribed_event(status):
                    pubnub.stop()
                    _test.stop()

            def presence(self, pubnub, presence):
                pass

        callback = MyCallback()
        self.pubnub.add_listener(callback)
        self.pubnub.subscribe().channels("ch1").execute()
        self.pubnub.start()
        self.wait()

    def _unsubscribe(self):
        self.pubnub.unsubscribe().channels(["ch1", "ch2"]).execute()
