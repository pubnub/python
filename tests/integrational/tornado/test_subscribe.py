import logging
import tornado
import pubnub as pn

from tornado.testing import AsyncTestCase
from pubnub.pubnub_tornado import PubNubTornado
from tests import helper
from tests.helper import pnconf_copy
from tests.integrational.tornado.tornado_helper import ExtendedSubscribeCallback

pn.set_stream_logger('pubnub', logging.DEBUG)

ch1 = "ch1"
ch2 = "ch2"


class SubscriptionTest(object):
    def __init__(self):
        super(SubscriptionTest, self).__init__()
        self.pubnub = None
        self.pubnub_listener = None


class TestSubscription(AsyncTestCase, SubscriptionTest):
    def setUp(self):
        super(TestSubscription, self).setUp()
        self.pubnub = PubNubTornado(pnconf_copy(), custom_ioloop=self.io_loop)
        self.pubnub_listener = PubNubTornado(pnconf_copy(), custom_ioloop=self.io_loop)

    @tornado.testing.gen_test()
    def test_subscribe_unsubscribe(self):
        callback_messages = ExtendedSubscribeCallback()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channels("ch1").execute()
        yield callback_messages.wait_for_connect()

        self.pubnub.unsubscribe().channels("ch1").execute()
        yield callback_messages.wait_for_disconnect()

    @tornado.testing.gen_test()
    def test_join_leave(self):
        self.pubnub.config.uuid = helper.gen_channel("messenger")
        self.pubnub_listener.config.uuid = helper.gen_channel("listener")
        callback_presence = ExtendedSubscribeCallback()
        self.pubnub_listener.add_listener(callback_presence)
        self.pubnub_listener.subscribe().channels("ch1").with_presence().execute()
        yield callback_presence.wait_for_connect()

        envelope = yield callback_presence.wait_for_presence_on("ch1")
        assert envelope.actual_channel == "ch1-pnpres"
        assert envelope.event == 'join'
        assert envelope.uuid == self.pubnub_listener.uuid

        callback_messages = ExtendedSubscribeCallback()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channels("ch1").execute()
        yield callback_messages.wait_for_connect()

        envelope = yield callback_presence.wait_for_presence_on("ch1")
        assert envelope.actual_channel == "ch1-pnpres"
        assert envelope.event == 'join'
        assert envelope.uuid == self.pubnub.uuid

        self.pubnub.unsubscribe().channels("ch1").execute()
        yield callback_messages.wait_for_disconnect()

        envelope = yield callback_presence.wait_for_presence_on("ch1")
        assert envelope.actual_channel == "ch1-pnpres"
        assert envelope.event == 'leave'
        assert envelope.uuid == self.pubnub.uuid

        self.pubnub_listener.unsubscribe().channels("ch1").execute()
        yield callback_presence.wait_for_disconnect()
        self.pubnub.stop()
        self.stop()
