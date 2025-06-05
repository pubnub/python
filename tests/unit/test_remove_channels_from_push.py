import unittest
import pytest
from pubnub.exceptions import PubNubException
from pubnub.pubnub import PubNub
from pubnub.endpoints.push.remove_channels_from_push import RemoveChannelsFromPush
from pubnub.enums import PNPushType, PNPushEnvironment
from tests.helper import mocked_config


class TestRemoveChannelsFromPush(unittest.TestCase):
    """Unit tests for the remove_channels_from_push method in PubNub core."""

    def test_remove_channels_from_push_with_named_parameters(self):
        """Test remove_channels_from_push with named parameters."""
        pubnub = PubNub(mocked_config)
        channels = ["alerts", "news", "updates"]
        device_id = "test_device_456"
        push_type = PNPushType.APNS2
        topic = "com.example.app.notifications"
        environment = PNPushEnvironment.DEVELOPMENT

        endpoint = pubnub.remove_channels_from_push(
            channels=channels,
            device_id=device_id,
            push_type=push_type,
            topic=topic,
            environment=environment
        )

        self.assertIsInstance(endpoint, RemoveChannelsFromPush)
        self.assertEqual(endpoint._channels, channels)
        self.assertEqual(endpoint._device_id, device_id)
        self.assertEqual(endpoint._push_type, push_type)
        self.assertEqual(endpoint._topic, topic)
        self.assertEqual(endpoint._environment, environment)

    def test_remove_channels_from_push_builder(self):
        """Test that the returned object supports method chaining."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.remove_channels_from_push() \
            .channels(["test_channel"]) \
            .device_id("test_device") \
            .push_type(PNPushType.GCM) \
            .topic("test_topic") \
            .environment(PNPushEnvironment.DEVELOPMENT)

        self.assertIsInstance(endpoint, RemoveChannelsFromPush)
        self.assertEqual(endpoint._channels, ["test_channel"])
        self.assertEqual(endpoint._device_id, "test_device")
        self.assertEqual(endpoint._push_type, PNPushType.GCM)

    def test_remove_channels_from_push_apns2_fails_without_topic(self):
        """Test that APNS2 fails validation when no topic is provided."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.remove_channels_from_push(
            channels=["test_channel"],
            device_id="test_device",
            push_type=PNPushType.APNS2
            # No topic provided - should fail validation
        )

        with pytest.raises(PubNubException) as exc_info:
            endpoint.validate_params()

        self.assertIn("Push notification topic is missing", str(exc_info.value))

    def test_remove_channels_from_push_none_push_type_validation(self):
        """Test that None push_type fails validation when required."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.remove_channels_from_push(
            channels=["test_channel"],
            device_id="test_device",
            push_type=None  # None push_type should fail validation
        )

        with pytest.raises(PubNubException) as exc_info:
            endpoint.validate_params()

        self.assertIn("Push Type is missing", str(exc_info.value))

    def test_remove_channels_from_push_none_device_id_validation(self):
        """Test that None device_id fails validation when required."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.remove_channels_from_push(
            channels=["test_channel"],
            device_id=None,  # None device_id should fail validation
            push_type=PNPushType.APNS
        )

        with pytest.raises(PubNubException) as exc_info:
            endpoint.validate_params()

        self.assertIn("Device ID is missing", str(exc_info.value))

    def test_remove_channels_from_push_none_channels_validation(self):
        """Test that None channels fails validation when required."""
        pubnub = PubNub(mocked_config)

        endpoint = pubnub.remove_channels_from_push(
            channels=None,  # None channels should fail validation
            device_id="test_device",
            push_type=PNPushType.APNS
        )

        with pytest.raises(PubNubException) as exc_info:
            endpoint.validate_params()

        self.assertIn("Channel missing", str(exc_info.value))