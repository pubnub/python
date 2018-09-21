import logging
import unittest
import time
import pubnub as pn

from pubnub.exceptions import PubNubException
from pubnub.models.consumer.channel_group import PNChannelGroupsAddChannelResult, PNChannelGroupsRemoveChannelResult
from pubnub.models.consumer.pubsub import PNPublishResult, PNMessageResult
from pubnub.pubnub import PubNub, SubscribeListener, NonSubscribeListener
from tests import helper
from tests.helper import pnconf_sub_copy


pn.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubSubscription(unittest.TestCase):
    def test_subscribe_unsubscribe(self):
        pubnub = PubNub(pnconf_sub_copy())
        ch = helper.gen_channel("test-subscribe-sub-unsub")

        try:
            listener = SubscribeListener()
            pubnub.add_listener(listener)

            pubnub.subscribe().channels(ch).execute()
            assert ch in pubnub.get_subscribed_channels()
            assert len(pubnub.get_subscribed_channels()) == 1

            listener.wait_for_connect()
            assert ch in pubnub.get_subscribed_channels()
            assert len(pubnub.get_subscribed_channels()) == 1

            pubnub.unsubscribe().channels(ch).execute()
            assert ch not in pubnub.get_subscribed_channels()
            assert len(pubnub.get_subscribed_channels()) == 0

            listener.wait_for_disconnect()
            assert ch not in pubnub.get_subscribed_channels()
            assert len(pubnub.get_subscribed_channels()) == 0

        except PubNubException as e:
            self.fail(e)
        finally:
            pubnub.stop()

    @unittest.skip("Test fails for unknown reason")
    def test_subscribe_pub_unsubscribe(self):
        ch = helper.gen_channel("test-subscribe-sub-pub-unsub")
        pubnub = PubNub(pnconf_sub_copy())
        subscribe_listener = SubscribeListener()
        publish_operation = NonSubscribeListener()
        message = "hey"

        try:
            pubnub.add_listener(subscribe_listener)

            pubnub.subscribe().channels(ch).execute()
            subscribe_listener.wait_for_connect()

            pubnub.publish().channel(ch).message(message).pn_async(publish_operation.callback)

            if publish_operation.pn_await() is False:
                self.fail("Publish operation timeout")

            publish_result = publish_operation.result
            assert isinstance(publish_result, PNPublishResult)
            assert publish_result.timetoken > 0

            result = subscribe_listener.wait_for_message_on(ch)
            assert isinstance(result, PNMessageResult)
            assert result.channel == ch
            assert result.subscription is None
            assert result.timetoken > 0
            assert result.message == message

            pubnub.unsubscribe().channels(ch).execute()
            subscribe_listener.wait_for_disconnect()
        except PubNubException as e:
            self.fail(e)
        finally:
            pubnub.stop()

    @unittest.skip("Test fails for unknown reason")
    def test_join_leave(self):
        ch = helper.gen_channel("test-subscribe-join-leave")

        pubnub = PubNub(pnconf_sub_copy())
        pubnub_listener = PubNub(pnconf_sub_copy())
        callback_messages = SubscribeListener()
        callback_presence = SubscribeListener()

        pubnub.config.uuid = helper.gen_channel("messenger")
        pubnub_listener.config.uuid = helper.gen_channel("listener")

        try:
            pubnub.add_listener(callback_messages)
            pubnub_listener.add_listener(callback_presence)

            pubnub_listener.subscribe().channels(ch).with_presence().execute()
            callback_presence.wait_for_connect()

            envelope = callback_presence.wait_for_presence_on(ch)
            assert envelope.channel == ch
            assert envelope.event == 'join'
            assert envelope.uuid == pubnub_listener.uuid

            pubnub.subscribe().channels(ch).execute()
            callback_messages.wait_for_connect()

            envelope = callback_presence.wait_for_presence_on(ch)
            assert envelope.channel == ch
            assert envelope.event == 'join'
            assert envelope.uuid == pubnub.uuid

            pubnub.unsubscribe().channels(ch).execute()
            callback_messages.wait_for_disconnect()

            envelope = callback_presence.wait_for_presence_on(ch)
            assert envelope.channel == ch
            assert envelope.event == 'leave'
            assert envelope.uuid == pubnub.uuid

            pubnub_listener.unsubscribe().channels(ch).execute()
            callback_presence.wait_for_disconnect()
        except PubNubException as e:
            self.fail(e)
        finally:
            pubnub.stop()
            pubnub_listener.stop()

    def test_cg_subscribe_unsubscribe(self):
        ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
        gr = helper.gen_channel("test-subscribe-unsubscribe-group")

        pubnub = PubNub(pnconf_sub_copy())
        callback_messages = SubscribeListener()
        cg_operation = NonSubscribeListener()

        pubnub.add_channel_to_channel_group()\
            .channel_group(gr)\
            .channels(ch)\
            .pn_async(cg_operation.callback)
        result = cg_operation.await_result()
        assert isinstance(result, PNChannelGroupsAddChannelResult)
        cg_operation.reset()

        time.sleep(1)

        pubnub.add_listener(callback_messages)
        pubnub.subscribe().channel_groups(gr).execute()
        callback_messages.wait_for_connect()

        pubnub.unsubscribe().channel_groups(gr).execute()
        callback_messages.wait_for_disconnect()

        pubnub.remove_channel_from_channel_group()\
            .channel_group(gr)\
            .channels(ch)\
            .pn_async(cg_operation.callback)
        result = cg_operation.await_result()
        assert isinstance(result, PNChannelGroupsRemoveChannelResult)

        pubnub.stop()

    def test_subscribe_cg_publish_unsubscribe(self):
        ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
        gr = helper.gen_channel("test-subscribe-unsubscribe-group")
        message = "hey"

        pubnub = PubNub(pnconf_sub_copy())
        callback_messages = SubscribeListener()
        non_subscribe_listener = NonSubscribeListener()

        pubnub.add_channel_to_channel_group() \
            .channel_group(gr) \
            .channels(ch) \
            .pn_async(non_subscribe_listener.callback)
        result = non_subscribe_listener.await_result_and_reset()
        assert isinstance(result, PNChannelGroupsAddChannelResult)

        time.sleep(1)

        pubnub.add_listener(callback_messages)
        pubnub.subscribe().channel_groups(gr).execute()
        callback_messages.wait_for_connect()

        pubnub.publish().message(message).channel(ch).pn_async(non_subscribe_listener.callback)
        result = non_subscribe_listener.await_result_and_reset()
        assert isinstance(result, PNPublishResult)
        assert result.timetoken > 0

        pubnub.unsubscribe().channel_groups(gr).execute()
        callback_messages.wait_for_disconnect()

        pubnub.remove_channel_from_channel_group() \
            .channel_group(gr) \
            .channels(ch) \
            .pn_async(non_subscribe_listener.callback)
        result = non_subscribe_listener.await_result_and_reset()
        assert isinstance(result, PNChannelGroupsRemoveChannelResult)

        pubnub.stop()

    @unittest.skip("Test fails for unknown reason")
    def test_subscribe_cg_join_leave(self):
        ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
        gr = helper.gen_channel("test-subscribe-unsubscribe-group")

        pubnub = PubNub(pnconf_sub_copy())
        pubnub_listener = PubNub(pnconf_sub_copy())
        non_subscribe_listener = NonSubscribeListener()

        pubnub.add_channel_to_channel_group() \
            .channel_group(gr) \
            .channels(ch) \
            .pn_async(non_subscribe_listener.callback)
        result = non_subscribe_listener.await_result_and_reset()
        assert isinstance(result, PNChannelGroupsAddChannelResult)

        time.sleep(1)

        callback_messages = SubscribeListener()
        callback_presence = SubscribeListener()

        pubnub_listener.add_listener(callback_presence)
        pubnub_listener.subscribe().channel_groups(gr).with_presence().execute()
        callback_presence.wait_for_connect()

        prs_envelope = callback_presence.wait_for_presence_on(ch)
        assert prs_envelope.event == 'join'
        assert prs_envelope.uuid == pubnub_listener.uuid
        assert prs_envelope.channel == ch
        assert prs_envelope.subscription == gr

        pubnub.add_listener(callback_messages)
        pubnub.subscribe().channel_groups(gr).execute()

        prs_envelope = callback_presence.wait_for_presence_on(ch)

        assert prs_envelope.event == 'join'
        assert prs_envelope.uuid == pubnub.uuid
        assert prs_envelope.channel == ch
        assert prs_envelope.subscription == gr

        pubnub.unsubscribe().channel_groups(gr).execute()
        prs_envelope = callback_presence.wait_for_presence_on(ch)

        assert prs_envelope.event == 'leave'
        assert prs_envelope.uuid == pubnub.uuid
        assert prs_envelope.channel == ch
        assert prs_envelope.subscription == gr

        pubnub_listener.unsubscribe().channel_groups(gr).execute()
        callback_presence.wait_for_disconnect()

        pubnub.remove_channel_from_channel_group() \
            .channel_group(gr) \
            .channels(ch) \
            .pn_async(non_subscribe_listener.callback)
        result = non_subscribe_listener.await_result_and_reset()
        assert isinstance(result, PNChannelGroupsRemoveChannelResult)

        pubnub.stop()
        pubnub_listener.stop()
