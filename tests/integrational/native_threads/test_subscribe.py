import binascii
import logging
import unittest
import time
import pubnub as pn

from pubnub.enums import PNStatusCategory
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.channel_group import PNChannelGroupsAddChannelResult, PNChannelGroupsRemoveChannelResult
from pubnub.models.consumer.pubsub import PNPublishResult, PNMessageResult
from pubnub.pubnub import PubNub, SubscribeListener, NonSubscribeListener
from tests import helper
from tests.helper import pnconf_enc_env_copy, pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


pn.set_stream_logger('pubnub', logging.DEBUG)


class DisconnectListener(SubscribeListener):
    status_result = None
    disconnected = False

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNDisconnectedCategory:
            print('Could not connect. Exiting...')
            self.disconnected = True

    def message(self, pubnub, message):
        print(f'Message:\n{message.__dict__}')

    def presence(self, pubnub, presence):
        print(f'Presence:\n{presence.__dict__}')


class TestPubNubSubscription(unittest.TestCase):
    def test_subscribe_unsubscribe(self):
        pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))
        ch = "test-subscribe-sub-unsub"

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

    def test_subscribe_pub_unsubscribe(self):
        ch = "test-subscribe-pub-unsubscribe"
        pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))
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

    def test_join_leave(self):
        ch = helper.gen_channel("test-subscribe-join-leave")
        pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))
        pubnub_listener = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))
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
        ch = "test-subscribe-unsubscribe-channel"
        gr = "test-subscribe-unsubscribe-group"

        pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))
        callback_messages = SubscribeListener()
        cg_operation = NonSubscribeListener()

        pubnub.add_channel_to_channel_group()\
            .channel_group(gr)\
            .channels(ch)\
            .pn_async(cg_operation.callback)
        result = cg_operation.await_result(1)
        if result is None:
            self.fail("Add channel to channel group operation timeout or failed")
        if cg_operation.status is not None and cg_operation.status.is_error():
            self.fail(f"Add channel to channel group operation failed with error: {cg_operation.status}")
        assert isinstance(result, PNChannelGroupsAddChannelResult)
        time.sleep(1)

        pubnub.add_listener(callback_messages)
        pubnub.subscribe().channel_groups(gr).execute()
        callback_messages.wait_for_connect()

        pubnub.unsubscribe().channel_groups(gr).execute()
        callback_messages.wait_for_disconnect()

        # Create a new listener for the remove operation to avoid potential race conditions
        cg_remove_operation = NonSubscribeListener()
        pubnub.remove_channel_from_channel_group()\
            .channel_group(gr)\
            .channels(ch)\
            .pn_async(cg_remove_operation.callback)
        result = cg_remove_operation.await_result(1)
        if result is None:
            self.fail("Remove channel from channel group operation timeout or failed")
        if cg_remove_operation.status is not None and cg_remove_operation.status.is_error():
            self.fail(f"Remove channel from channel group operation failed with error: {cg_remove_operation.status}")
        assert isinstance(result, PNChannelGroupsRemoveChannelResult)

        pubnub.stop()

    def test_subscribe_cg_publish_unsubscribe(self):
        ch = "test-subscribe-unsubscribe-channel"
        gr = "test-subscribe-unsubscribe-group"
        message = "hey"

        pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))
        callback_messages = SubscribeListener()
        non_subscribe_listener = NonSubscribeListener()

        pubnub.add_channel_to_channel_group() \
            .channel_group(gr) \
            .channels(ch) \
            .pn_async(non_subscribe_listener.callback)
        result = non_subscribe_listener.await_result_and_reset(1)
        if result is None:
            self.fail("Add channel to channel group operation timeout or failed")
        if non_subscribe_listener.status is not None and non_subscribe_listener.status.is_error():
            self.fail(f"Add channel to channel group operation failed with error: {non_subscribe_listener.status}")
        assert isinstance(result, PNChannelGroupsAddChannelResult)
        non_subscribe_listener.reset()
        time.sleep(1)

        pubnub.add_listener(callback_messages)
        pubnub.subscribe().channel_groups(gr).execute()
        callback_messages.wait_for_connect()

        pubnub.publish().message(message).channel(ch).pn_async(non_subscribe_listener.callback)
        result = non_subscribe_listener.await_result_and_reset(10)
        if result is None:
            print(f"Debug: non_subscribe_listener.status = {non_subscribe_listener.status}")
            if non_subscribe_listener.status is not None:
                print(f"Debug: status.is_error() = {non_subscribe_listener.status.is_error()}")
                print(f"Debug: status.category = {non_subscribe_listener.status.category}")
                print(f"Debug: status.error_data = {non_subscribe_listener.status.error_data}")
            self.fail("Publish operation timeout or failed")
        if non_subscribe_listener.status is not None and non_subscribe_listener.status.is_error():
            self.fail(f"Publish operation failed with error: {non_subscribe_listener.status}")
        assert isinstance(result, PNPublishResult)
        assert result.timetoken > 0

        pubnub.unsubscribe().channel_groups(gr).execute()
        callback_messages.wait_for_disconnect()

        pubnub.remove_channel_from_channel_group() \
            .channel_group(gr) \
            .channels(ch) \
            .pn_async(non_subscribe_listener.callback)
        result = non_subscribe_listener.await_result_and_reset(1)
        if result is None:
            self.fail("Remove channel from channel group operation timeout or failed")
        if non_subscribe_listener.status is not None and non_subscribe_listener.status.is_error():
            self.fail(f"Remove channel from channel group operation failed with error: {non_subscribe_listener.status}")
        assert isinstance(result, PNChannelGroupsRemoveChannelResult)

        pubnub.stop()

    def test_subscribe_cg_join_leave(self):
        ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
        gr = helper.gen_channel("test-subscribe-unsubscribe-group")
        pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))
        pubnub_listener = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))
        callback_messages = SubscribeListener()
        callback_presence = SubscribeListener()

        result = pubnub.add_channel_to_channel_group() \
            .channel_group(gr) \
            .channels(ch) \
            .sync()

        assert isinstance(result.result, PNChannelGroupsAddChannelResult)
        time.sleep(1)

        pubnub.config.uuid = helper.gen_channel("messenger")
        pubnub_listener.config.uuid = helper.gen_channel("listener")

        pubnub.add_listener(callback_messages)
        pubnub_listener.add_listener(callback_presence)

        pubnub_listener.subscribe().channel_groups(gr).with_presence().execute()
        callback_presence.wait_for_connect()

        envelope = callback_presence.wait_for_presence_on(ch)
        assert envelope.channel == ch
        assert envelope.event == 'join'
        assert envelope.uuid == pubnub_listener.uuid

        pubnub.subscribe().channel_groups(gr).execute()
        callback_messages.wait_for_connect()

        envelope = callback_presence.wait_for_presence_on(ch)
        assert envelope.channel == ch
        assert envelope.event == 'join'
        assert envelope.uuid == pubnub.uuid

        pubnub.unsubscribe().channel_groups(gr).execute()
        callback_messages.wait_for_disconnect()

        envelope = callback_presence.wait_for_presence_on(ch)
        assert envelope.channel == ch
        assert envelope.event == 'leave'
        assert envelope.uuid == pubnub.uuid

        pubnub_listener.unsubscribe().channel_groups(gr).execute()
        callback_presence.wait_for_disconnect()

        result = pubnub.remove_channel_from_channel_group() \
            .channel_group(gr) \
            .channels(ch) \
            .sync()
        assert isinstance(result.result, PNChannelGroupsRemoveChannelResult)

        pubnub.stop()
        pubnub_listener.stop()

    def test_subscribe_pub_unencrypted_unsubscribe(self):
        ch = helper.gen_channel("test-subscribe-pub-unencrypted-unsubscribe")

        pubnub_plain = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))
        pubnub = PubNub(pnconf_enc_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True))

        subscribe_listener = SubscribeListener()
        publish_operation = NonSubscribeListener()
        metadata = {'test': 'publish'}
        custom_message_type = "test"
        message = "hey"

        try:
            pubnub.add_listener(subscribe_listener)

            pubnub.subscribe().channels(ch).execute()
            subscribe_listener.wait_for_connect()

            pubnub_plain.publish() \
                .channel(ch) \
                .message(message) \
                .custom_message_type(custom_message_type) \
                .meta(metadata) \
                .pn_async(publish_operation.callback)

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
            assert result.custom_message_type == custom_message_type
            assert result.user_metadata == metadata
            assert result.error is not None
            assert isinstance(result.error, binascii.Error)

            pubnub.unsubscribe().channels(ch).execute()
            subscribe_listener.wait_for_disconnect()
        except PubNubException as e:
            self.fail(e)
        finally:
            pubnub.stop()
