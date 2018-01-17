import logging

import tornado
from tornado import gen
from tornado.testing import AsyncTestCase

import pubnub as pn
from pubnub.pubnub_tornado import PubNubTornado, SubscribeListener
from tests.helper import pnconf_sub_copy
from tests.integrational.tornado.vcr_tornado_decorator import use_cassette_and_stub_time_sleep

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

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/subscribe/sub_unsub.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test(timeout=300)
    def test_subscribe_unsubscribe(self):
        ch = "subscribe-tornado-ch"

        callback_messages = SubscribeListener()
        self.pubnub.add_listener(callback_messages)

        self.pubnub.subscribe().channels(ch).execute()
        assert ch in self.pubnub.get_subscribed_channels()
        assert len(self.pubnub.get_subscribed_channels()) == 1

        yield callback_messages.wait_for_connect()
        assert ch in self.pubnub.get_subscribed_channels()
        assert len(self.pubnub.get_subscribed_channels()) == 1

        self.pubnub.unsubscribe().channels(ch).execute()
        assert ch not in self.pubnub.get_subscribed_channels()
        assert len(self.pubnub.get_subscribed_channels()) == 0

        yield callback_messages.wait_for_disconnect()
        assert ch not in self.pubnub.get_subscribed_channels()
        assert len(self.pubnub.get_subscribed_channels()) == 0

        self.pubnub.stop()
        self.stop()

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/subscribe/sub_pub_unsub.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'])
    @tornado.testing.gen_test(timeout=30)
    def test_subscribe_publish_unsubscribe(self):
        ch = "subscribe-tornado-ch"
        message = "hey"

        callback_messages = SubscribeListener()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channels(ch).execute()
        yield callback_messages.wait_for_connect()

        sub_env, pub_env = yield [
            callback_messages.wait_for_message_on(ch),
            self.pubnub.publish().channel(ch).message(message).future()]

        assert pub_env.status.original_response[0] == 1
        assert pub_env.status.original_response[1] == 'Sent'

        assert sub_env.channel == ch
        assert sub_env.subscription is None
        assert sub_env.message == message

        self.pubnub.unsubscribe().channels(ch).execute()
        yield callback_messages.wait_for_disconnect()

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/subscribe/join_leave.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test(timeout=30)
    def test_join_leave(self):
        ch = "subscribe-tornado-ch"

        # HINT: use random generated uuids to test without VCR
        # rnd = gen_string(4)
        # self.pubnub.config.uuid = "subscribe-tornado-messenger-%s" % rnd
        # self.pubnub_listener.config.uuid = "subscribe-tornado-listener-%s" % rnd

        self.pubnub.config.uuid = "subscribe-tornado-messenger-3"
        self.pubnub_listener.config.uuid = "subscribe-tornado-listener-3"

        callback_presence = SubscribeListener()
        self.pubnub_listener.add_listener(callback_presence)
        self.pubnub_listener.subscribe().channels(ch).with_presence().execute()
        yield callback_presence.wait_for_connect()

        envelope = yield callback_presence.wait_for_presence_on(ch)
        assert envelope.channel == ch
        assert envelope.event == 'join'
        assert envelope.uuid == self.pubnub_listener.uuid

        callback_messages = SubscribeListener()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channels(ch).execute()
        yield callback_messages.wait_for_connect()

        envelope = yield callback_presence.wait_for_presence_on(ch)
        assert envelope.channel == ch
        assert envelope.event == 'join'
        assert envelope.uuid == self.pubnub.uuid

        self.pubnub.unsubscribe().channels(ch).execute()
        yield callback_messages.wait_for_disconnect()

        envelope = yield callback_presence.wait_for_presence_on(ch)
        assert envelope.channel == ch
        assert envelope.event == 'leave'
        assert envelope.uuid == self.pubnub.uuid

        self.pubnub_listener.unsubscribe().channels(ch).execute()
        yield callback_presence.wait_for_disconnect()
        self.pubnub.stop()
        self.stop()


class TestChannelGroupSubscription(AsyncTestCase, SubscriptionTest):
    def setUp(self):
        super(TestChannelGroupSubscription, self).setUp()
        self.pubnub = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)
        self.pubnub_listener = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/subscribe/group_sub_unsub.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_cg', 'l_pres'])
    @tornado.testing.gen_test(timeout=60)
    def test_group_subscribe_unsubscribe(self):
        ch = "subscribe-unsubscribe-channel"
        gr = "subscribe-unsubscribe-group"

        envelope = yield self.pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

        yield gen.sleep(1)

        callback_messages = SubscribeListener()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channel_groups(gr).execute()
        yield callback_messages.wait_for_connect()

        self.pubnub.unsubscribe().channel_groups(gr).execute()
        yield callback_messages.wait_for_disconnect()

        envelope = yield self.pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/subscribe/group_sub_pub_unsub.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_cg', 'l_pub', 'l_pres'])
    @tornado.testing.gen_test(timeout=60)
    def test_group_subscribe_publish_unsubscribe(self):
        ch = "subscribe-unsubscribe-channel"
        gr = "subscribe-unsubscribe-group"
        message = "hey"

        envelope = yield self.pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

        yield gen.sleep(1)

        callback_messages = SubscribeListener()
        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channel_groups(gr).execute()
        yield callback_messages.wait_for_connect()

        sub_envelope, pub_envelope = yield [
            callback_messages.wait_for_message_on(ch),
            self.pubnub.publish().channel(ch).message(message).future()]

        assert pub_envelope.status.original_response[0] == 1
        assert pub_envelope.status.original_response[1] == 'Sent'

        assert sub_envelope.channel == ch
        assert sub_envelope.subscription == gr
        assert sub_envelope.message == message

        self.pubnub.unsubscribe().channel_groups(gr).execute()
        yield callback_messages.wait_for_disconnect()

        envelope = yield self.pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/subscribe/group_join_leave.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_cg', 'l_pres'])
    @tornado.testing.gen_test(timeout=60)
    def test_group_join_leave(self):
        self.pubnub.config.uuid = "test-subscribe-messenger"
        self.pubnub_listener.config.uuid = "test-subscribe-listener"

        ch = "subscribe-test-channel"
        gr = "subscribe-test-group"

        envelope = yield self.pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

        yield gen.sleep(1)

        callback_messages = SubscribeListener()
        callback_presence = SubscribeListener()

        self.pubnub_listener.add_listener(callback_presence)
        self.pubnub_listener.subscribe().channel_groups(gr).with_presence().execute()
        yield callback_presence.wait_for_connect()

        prs_envelope = yield callback_presence.wait_for_presence_on(ch)
        assert prs_envelope.event == 'join'
        assert prs_envelope.uuid == self.pubnub_listener.uuid
        assert prs_envelope.channel == ch
        assert prs_envelope.subscription == gr

        self.pubnub.add_listener(callback_messages)
        self.pubnub.subscribe().channel_groups(gr).execute()

        useless, prs_envelope = yield [
            callback_messages.wait_for_connect(),
            callback_presence.wait_for_presence_on(ch)
        ]

        assert prs_envelope.event == 'join'
        assert prs_envelope.uuid == self.pubnub.uuid
        assert prs_envelope.channel == ch
        assert prs_envelope.subscription == gr

        self.pubnub.unsubscribe().channel_groups(gr).execute()

        useless, prs_envelope = yield [
            callback_messages.wait_for_disconnect(),
            callback_presence.wait_for_presence_on(ch)
        ]

        assert prs_envelope.event == 'leave'
        assert prs_envelope.uuid == self.pubnub.uuid
        assert prs_envelope.channel == ch
        assert prs_envelope.subscription == gr

        self.pubnub_listener.unsubscribe().channel_groups(gr).execute()
        yield callback_presence.wait_for_disconnect()

        envelope = yield self.pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
        assert envelope.status.original_response['status'] == 200

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/subscribe/subscribe_tep_by_step.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pres'])
    @tornado.testing.gen_test(timeout=30)
    def test_subscribe_step_by_step(self):
        ch1 = 'test-here-now-channel1'
        ch2 = 'test-here-now-channel2'
        ch3 = 'test-here-now-channel3'
        self.pubnub.config.uuid = 'test-here-now-uuid'
        callback_messages = SubscribeListener()
        self.pubnub.add_listener(callback_messages)
        print("connecting to the first...")
        self.pubnub.subscribe().channels(ch1).execute()
        yield callback_messages.wait_for_connect()
        print("...connected to the first")
        yield gen.sleep(1)
        print("connecting to the second...")
        self.pubnub.subscribe().channels(ch2).execute()
        self.pubnub.subscribe().channels(ch3).execute()
        self.pubnub.subscribe().channels(ch3).execute()
        self.pubnub.subscribe().channels(ch2).execute()
        print("...connected to the second")
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

        self.pubnub.unsubscribe().channels([ch1, ch2]).execute()
        yield callback_messages.wait_for_disconnect()

        self.pubnub.unsubscribe().channels(ch3).execute()

        self.pubnub.stop()
        self.stop()
