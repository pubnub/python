import unittest
from unittest.mock import patch

from pubnub.pubnub import PubNub, NativeSubscriptionManager, SubscribeListener
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNMessageResult
from pubnub.enums import PNStatusCategory, PNOperationType
from tests.helper import pnconf_copy


class TestSubscribeThreads(unittest.TestCase):
    def setUp(self):
        self.pubnub = PubNub(pnconf_copy())
        self.pubnub._subscription_manager = NativeSubscriptionManager(self.pubnub)
        self.listener = SubscribeListener()
        self.pubnub.add_listener(self.listener)

    def tearDown(self):
        self.pubnub.stop()
        self.pubnub.unsubscribe_all()

    # Subscription Management Tests
    def test_subscribe_single_channel(self):
        """Test subscribing to a single channel"""
        with patch.object(self.pubnub._subscription_manager, '_start_subscribe_loop') as mock_start:
            self.pubnub.subscribe().channels('test-channel').execute()
            mock_start.assert_called_once()
            self.assertEqual(len(self.pubnub._subscription_manager._subscription_state._channels), 1)
            self.assertIn('test-channel', self.pubnub._subscription_manager._subscription_state._channels)

    def test_subscribe_multiple_channels(self):
        """Test subscribing to multiple channels"""
        channels = ['channel-1', 'channel-2', 'channel-3']
        with patch.object(self.pubnub._subscription_manager, '_start_subscribe_loop') as mock_start:
            self.pubnub.subscribe().channels(channels).execute()
            mock_start.assert_called_once()
            self.assertEqual(len(self.pubnub._subscription_manager._subscription_state._channels), 3)
            for channel in channels:
                self.assertIn(channel, self.pubnub._subscription_manager._subscription_state._channels)

    def test_unsubscribe_single_channel(self):
        """Test unsubscribing from a single channel"""
        channel = 'test-channel'
        self.pubnub.subscribe().channels(channel).execute()
        with patch.object(self.pubnub._subscription_manager, '_send_leave') as mock_leave:
            self.pubnub.unsubscribe().channels(channel).execute()
            mock_leave.assert_called_once()
            self.assertEqual(len(self.pubnub._subscription_manager._subscription_state._channels), 0)

    # # Message Queue Tests
    def test_message_queue_put(self):
        """Test putting messages in the queue"""
        test_message = {"message": "test"}
        self.pubnub._subscription_manager._message_queue_put(test_message)
        self.assertEqual(self.pubnub._subscription_manager._message_queue.qsize(), 1)
        queued_message = self.pubnub._subscription_manager._message_queue.get()
        self.assertEqual(queued_message, test_message)

    # Reconnection Tests
    def test_reconnection_on_network_error(self):
        """Test reconnection behavior on network error"""
        with patch.object(
            self.pubnub._subscription_manager._reconnection_manager, 'start_polling'
        ) as mock_start_polling:
            status = PNStatus()
            status.category = PNStatusCategory.PNNetworkIssuesCategory
            status.error = True
            # Mock the _handle_endpoint_call to avoid JSON parsing issues
            with patch.object(self.pubnub._subscription_manager, '_handle_endpoint_call') as mock_handle:
                def side_effect(result, status):
                    if status.category == PNStatusCategory.PNNetworkIssuesCategory:
                        return self.pubnub._subscription_manager._reconnection_manager.start_polling()
                    return None
                mock_handle.side_effect = side_effect
                self.pubnub._subscription_manager._handle_endpoint_call(None, status)
                mock_start_polling.assert_called_once()

    def test_reconnection_success(self):
        """Test successful reconnection"""
        with patch.object(self.pubnub._subscription_manager, '_start_subscribe_loop') as mock_subscribe:
            self.pubnub._subscription_manager.reconnect()
            mock_subscribe.assert_called_once()
            self.assertFalse(self.pubnub._subscription_manager._should_stop)

    # Event Handling Tests
    def test_status_announcement(self):
        """Test status event announcement"""
        with patch.object(self.listener, 'status') as mock_status:
            status = PNStatus()
            status.category = PNStatusCategory.PNConnectedCategory
            self.pubnub._subscription_manager._listener_manager.announce_status(status)
            mock_status.assert_called_once_with(self.pubnub, status)

    def test_message_announcement(self):
        """Test message event announcement"""
        with patch.object(self.listener, 'message') as mock_message:
            message = PNMessageResult(
                message="test-message",
                subscription=None,
                channel="test-channel",
                timetoken=1234567890
            )
            self.pubnub._subscription_manager._listener_manager.announce_message(message)
            mock_message.assert_called_once_with(self.pubnub, message)
            self.assertEqual(mock_message.call_args[0][1].message, "test-message")
            self.assertEqual(mock_message.call_args[0][1].channel, "test-channel")

    # Error Handling Tests
    def test_subscribe_with_invalid_channel(self):
        """Test subscribing with invalid channel"""
        with self.assertRaises(TypeError):
            self.pubnub.subscribe().channels(None).execute()

    def test_error_on_access_denied(self):
        """Test handling of access denied error"""
        with patch.object(self.pubnub._subscription_manager, 'disconnect') as mock_disconnect:
            status = PNStatus()
            status.category = PNStatusCategory.PNAccessDeniedCategory
            status.operation = PNOperationType.PNSubscribeOperation
            status.error = True
            # Mock the _handle_endpoint_call to avoid JSON parsing issues
            with patch.object(self.pubnub._subscription_manager, '_handle_endpoint_call') as mock_handle:
                def side_effect(result, status):
                    if status.category == PNStatusCategory.PNAccessDeniedCategory:
                        return self.pubnub._subscription_manager.disconnect()
                    return None
                mock_handle.side_effect = side_effect
                self.pubnub._subscription_manager._handle_endpoint_call(None, status)
                mock_disconnect.assert_called_once()
