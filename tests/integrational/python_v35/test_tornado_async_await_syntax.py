import logging
import tornado
import pubnub as pn

from tornado.testing import AsyncTestCase
from pubnub.pubnub_tornado import PubNubTornado, SubscribeListener
from tests import helper
from tests.helper import pnconf_sub_copy

pn.set_stream_logger('pubnub', logging.DEBUG)


class SubscriptionTest(object):
    def __init__(self):
        super(SubscriptionTest, self).__init__()
        self.pubnub = None
        self.pubnub_listener = None


class TestChannelSubscription(AsyncTestCase, SubscriptionTest):
    def setUp(self):
        super(TestChannelSubscription, self).setUp()
        self.pubnub = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)
        self.pubnub_listener = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)

    @tornado.testing.gen_test
    async def test_subscribe_publish_unsubscribe(self):
        ch = helper.gen_channel("subscribe-test")
        message = "hey"

        callback_messages = SubscribeListener()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channels(ch).execute()
        await callback_messages.wait_for_connect()

        sub_env, pub_env = await tornado.gen.multi([
            callback_messages.wait_for_message_on(ch),
            self.pubnub.publish().channel(ch).message(message).future()])

        assert pub_env.status.original_response[0] == 1
        assert pub_env.status.original_response[1] == 'Sent'

        assert sub_env.channel == ch
        assert sub_env.subscription is None
        assert sub_env.message == message

        self.pubnub.unsubscribe().channels(ch).execute()
        await callback_messages.wait_for_disconnect()
