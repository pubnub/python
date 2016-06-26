import logging
import tornado
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

    @tornado.testing.gen_test(timeout=30)
    def test_subscribe_publish_unsubscribe(self):
        ch = helper.gen_channel("subscribe-test")
        message = "hey"

        callback_messages = ExtendedSubscribeCallback()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channels(ch).execute()
        yield callback_messages.wait_for_connect()

        sub_env, pub_env = yield [
            callback_messages.wait_for_message_on(ch),
            self.pubnub.publish().channel(ch).message(message).future()]

        assert pub_env.status.original_response[0] == 1
        assert pub_env.status.original_response[1] == 'Sent'

        assert sub_env.actual_channel == ch
        assert sub_env.subscribed_channel == ch
        assert sub_env.message == message

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


class TestChannelGroupSubscription(AsyncTestCase, SubscriptionTest):
    def setUp(self):
        super(TestChannelGroupSubscription, self).setUp()
        self.pubnub = PubNubTornado(pnconf_copy(), custom_ioloop=self.io_loop)
        self.pubnub_listener = PubNubTornado(pnconf_copy(), custom_ioloop=self.io_loop)

    @tornado.testing.gen_test(timeout=30)
    def test_subscribe_unsubscribe(self):
        ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
        gr = helper.gen_channel("test-subscribe-unsubscirbe-group")

        envelope = yield self.pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

        yield gen.sleep(1)

        callback_messages = ExtendedSubscribeCallback()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channel_groups(gr).execute()
        yield callback_messages.wait_for_connect()

        self.pubnub.unsubscribe().channel_groups(gr).execute()
        yield callback_messages.wait_for_disconnect()

        envelope = yield self.pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

    @tornado.testing.gen_test(timeout=30)
    def test_subscribe_publish_unsubscribe(self):
        ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
        gr = helper.gen_channel("test-subscribe-unsubscirbe-group")
        message = "hey"

        envelope = yield self.pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

        yield gen.sleep(1)

        callback_messages = ExtendedSubscribeCallback()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channel_groups(gr).execute()
        yield callback_messages.wait_for_connect()

        sub_envelope, pub_envelope = yield [
            callback_messages.wait_for_message_on(ch),
            self.pubnub.publish().channel(ch).message(message).future()]

        assert pub_envelope.status.original_response[0] == 1
        assert pub_envelope.status.original_response[1] == 'Sent'

        assert sub_envelope.actual_channel == ch
        assert sub_envelope.subscribed_channel == gr
        assert sub_envelope.message == message

        self.pubnub.unsubscribe().channel_groups(gr).execute()
        yield callback_messages.wait_for_disconnect()

        envelope = yield self.pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

    @tornado.testing.gen_test(timeout=30)
    def test_join_leave(self):
        self.pubnub.config.uuid = helper.gen_channel("messenger")
        self.pubnub_listener.config.uuid = helper.gen_channel("listener")

        ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
        gr = helper.gen_channel("test-subscribe-unsubscirbe-group")

        envelope = yield self.pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

        yield gen.sleep(1)

        callback_messages = ExtendedSubscribeCallback()
        callback_presence = ExtendedSubscribeCallback()

        self.pubnub_listener.add_listener(callback_presence)
        self.pubnub_listener.subscribe().channel_groups(gr).with_presence().execute()
        yield callback_presence.wait_for_connect()

        prs_envelope = yield callback_presence.wait_for_presence_on(ch)
        assert prs_envelope.event == 'join'
        assert prs_envelope.uuid == self.pubnub_listener.uuid
        assert prs_envelope.actual_channel == ch + "-pnpres"
        assert prs_envelope.subscribed_channel == gr + "-pnpres"

        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channel_groups(gr).execute()

        useless, prs_envelope = yield [
            callback_messages.wait_for_connect(),
            callback_presence.wait_for_presence_on(ch)
        ]

        assert prs_envelope.event == 'join'
        assert prs_envelope.uuid == self.pubnub.uuid
        assert prs_envelope.actual_channel == ch + "-pnpres"
        assert prs_envelope.subscribed_channel == gr + "-pnpres"

        self.pubnub.unsubscribe().channel_groups(gr).execute()

        useless, prs_envelope = yield [
            callback_messages.wait_for_disconnect(),
            callback_presence.wait_for_presence_on(ch)
        ]

        assert prs_envelope.event == 'leave'
        assert prs_envelope.uuid == self.pubnub.uuid
        assert prs_envelope.actual_channel == ch + "-pnpres"
        assert prs_envelope.subscribed_channel == gr + "-pnpres"

        self.pubnub_listener.unsubscribe().channel_groups(gr).execute()
        yield callback_presence.wait_for_disconnect()

        envelope = yield self.pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200
