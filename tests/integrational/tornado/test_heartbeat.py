import logging
import tornado.testing
import pubnub as pn

from tornado.testing import AsyncTestCase
from tornado import gen
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


class TestChannelSubscription(AsyncTestCase, SubscriptionTest):
    def setUp(self):
        super(TestChannelSubscription, self).setUp()

        messenger_config = pnconf_copy()
        messenger_config.set_presence_timeout(8)
        messenger_config.uuid = helper.gen_channel("messenger")

        listener_config = pnconf_copy()
        listener_config.uuid = helper.gen_channel("listener")

        self.pubnub = PubNubTornado(messenger_config, custom_ioloop=self.io_loop)
        self.pubnub_listener = PubNubTornado(listener_config, custom_ioloop=self.io_loop)
        self.pubnub.config.uuid = helper.gen_channel("messenger")
        self.pubnub_listener.config.uuid = helper.gen_channel("listener")

    @tornado.testing.gen_test(timeout=20)
    def test_timeout_event_on_broken_heartbeat(self):
        ch = helper.gen_channel("heartbeat-test")

        # - connect to :ch-pnpres
        callback_presence = ExtendedSubscribeCallback()
        self.pubnub_listener.add_listener(callback_presence)
        self.pubnub_listener.subscribe().channels(ch).with_presence().execute()
        yield callback_presence.wait_for_connect()

        envelope = yield callback_presence.wait_for_presence_on(ch)
        assert ch + "-pnpres" == envelope.actual_channel
        assert 'join' == envelope.event
        assert self.pubnub_listener.uuid == envelope.uuid

        # - connect to :ch
        callback_messages = ExtendedSubscribeCallback()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channels(ch).execute()

        # - assert join event
        useless, prs_envelope = yield [
            callback_messages.wait_for_connect(),
            callback_presence.wait_for_presence_on(ch)]
        assert ch + "-pnpres" == prs_envelope.actual_channel
        assert 'join' == prs_envelope.event
        assert self.pubnub.uuid == prs_envelope.uuid

        # wait for one heartbeat call
        yield gen.sleep(8)

        # - break messenger heartbeat loop
        self.pubnub._subscription_manager._stop_heartbeat_timer()

        # - assert for timeout
        envelope = yield callback_presence.wait_for_presence_on(ch)
        assert ch + "-pnpres" == envelope.actual_channel
        assert 'timeout' == envelope.event
        assert self.pubnub.uuid == envelope.uuid

        # - disconnect from :ch-pnpres
        self.pubnub_listener.unsubscribe().channels(ch).execute()
        yield callback_presence.wait_for_disconnect()
