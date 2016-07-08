import logging
import unittest
import pubnub as pn

from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult, PNMessageResult
from pubnub.pubnub import PubNub, SubscribeListener, NonSubscribeListener
from tests import helper
from tests.helper import pnconf_sub_copy


pn.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubSubscribe(unittest.TestCase):
    def test_subscribe_unsubscribe(self):
        pubnub = PubNub(pnconf_sub_copy())
        ch = helper.gen_channel("test-subscribe-sub-unsub")

        try:
            listener = SubscribeListener()
            pubnub.add_listener(listener)

            pubnub.subscribe().channels(ch).execute()
            listener.wait_for_connect()

            pubnub.unsubscribe().channels(ch).execute()
            listener.wait_for_disconnect()
        except PubNubException as e:
            self.fail(e)
        finally:
            pubnub.stop()

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

            pubnub.publish().channel(ch).message(message).async(publish_operation.callback)
            if not publish_operation.await():
                self.fail("Publish operation timeout")

            publish_result = publish_operation.result
            assert isinstance(publish_result, PNPublishResult)
            assert publish_result.timetoken > 0

            result = subscribe_listener.wait_for_message_on(ch)
            assert isinstance(result, PNMessageResult)
            assert result.actual_channel == ch
            assert result.subscribed_channel == ch
            assert result.timetoken > 0
            assert result.message == message

            pubnub.unsubscribe().channels(ch).execute()
            subscribe_listener.wait_for_disconnect()
        except PubNubException as e:
            self.fail(e)
        finally:
            pubnub.stop()

    def test_join_leave(self):
        ch = helper.gen_channel("test-subscribe-join-leave")
        ch_pnpres = ch + "-pnpres"

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
            assert envelope.actual_channel == ch_pnpres
            assert envelope.event == 'join'
            assert envelope.uuid == pubnub_listener.uuid

            pubnub.subscribe().channels(ch).execute()
            callback_messages.wait_for_connect()

            envelope = callback_presence.wait_for_presence_on(ch)
            assert envelope.actual_channel == ch_pnpres
            assert envelope.event == 'join'
            assert envelope.uuid == pubnub.uuid

            pubnub.unsubscribe().channels(ch).execute()
            callback_messages.wait_for_disconnect()

            envelope = callback_presence.wait_for_presence_on(ch)
            assert envelope.actual_channel == ch_pnpres
            assert envelope.event == 'leave'
            assert envelope.uuid == pubnub.uuid

            pubnub_listener.unsubscribe().channels(ch).execute()
            callback_presence.wait_for_disconnect()
        except PubNubException as e:
            self.fail(e)
        finally:
            pubnub.stop()
            pubnub_listener.stop()
