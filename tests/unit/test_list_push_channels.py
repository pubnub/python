import unittest

import pytest

from pubnub.exceptions import PubNubException
from pubnub.pubnub import PubNub
from pubnub.endpoints.push.list_push_provisions import ListPushProvisions
from pubnub.enums import PNPushType, PNPushEnvironment
from tests.helper import mocked_config


class TestListPushChannels(unittest.TestCase):
    """Unit tests for the list_push_channels method in PubNub core."""

    def test_list_push_channels_with_named_parameters(self):
        """Test list_push_channels with named parameters."""
        pubnub = PubNub(mocked_config)
        device_id = "test_device_456"
        push_type = PNPushType.APNS2
        topic = "com.example.app.notifications"
        environment = PNPushEnvironment.DEVELOPMENT

        endpoint = pubnub.list_push_channels(
            device_id=device_id,
            push_type=push_type,
            topic=topic,
            environment=environment
        )

        self.assertIsInstance(endpoint, ListPushProvisions)
        self.assertEqual(endpoint._device_id, device_id)
        self.assertEqual(endpoint._push_type, push_type)
        self.assertEqual(endpoint._topic, topic)
        self.assertEqual(endpoint._environment, environment)

    def test_list_push_channels_builder_gcm(self):
        """Test that the returned object supports method chaining."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.list_push_channels() \
            .device_id("test_device") \
            .push_type(PNPushType.GCM) \
            .topic("test_topic") \
            .environment(PNPushEnvironment.DEVELOPMENT)

        self.assertIsInstance(endpoint, ListPushProvisions)
        self.assertEqual(endpoint._device_id, "test_device")
        self.assertEqual(endpoint._push_type, PNPushType.GCM)

    def test_list_push_channels_builder_fcm(self):
        """Test that the returned object supports method chaining."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.list_push_channels() \
            .device_id("test_device") \
            .push_type(PNPushType.FCM) \
            .topic("test_topic") \
            .environment(PNPushEnvironment.DEVELOPMENT)

        self.assertIsInstance(endpoint, ListPushProvisions)
        self.assertEqual(endpoint._device_id, "test_device")
        self.assertEqual(endpoint._push_type, PNPushType.FCM)

    def test_list_push_channels_apns2_fails_without_topic(self):
        """Test that APNS2 fails validation when no topic is provided."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.list_push_channels(
            device_id="test_device",
            push_type=PNPushType.APNS2
            # No topic provided - should fail validation
        )

        with pytest.raises(PubNubException) as exc_info:
            endpoint.validate_params()

        self.assertIn("Push notification topic is missing", str(exc_info.value))

    def test_list_push_channels_none_push_type_validation(self):
        """Test that None push_type fails validation when required."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.list_push_channels(
            device_id="test_device",
            push_type=None  # None push_type should fail validation
        )

        with pytest.raises(PubNubException) as exc_info:
            endpoint.validate_params()

        self.assertIn("Push Type is missing", str(exc_info.value))

    def test_list_push_channels_none_device_id_validation(self):
        """Test that None device_id fails validation when required."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.list_push_channels(
            device_id=None,  # None device_id should fail validation
            push_type=PNPushType.APNS
        )

        with pytest.raises(PubNubException) as exc_info:
            endpoint.validate_params()

        self.assertIn("Device ID is missing", str(exc_info.value))
