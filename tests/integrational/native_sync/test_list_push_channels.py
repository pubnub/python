import unittest

from pubnub.pubnub import PubNub
from pubnub.enums import PNPushType, PNPushEnvironment
from pubnub.exceptions import PubNubException
from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


class TestListPushChannelsIntegration(unittest.TestCase):
    """Integration tests for list_push_channels endpoint."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.pubnub = PubNub(pnconf_env_copy(uuid="test-uuid"))

    def tearDown(self):
        """Clean up after each test method."""
        pass

    # ==============================================
    # BASIC FUNCTIONALITY TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/apns_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_apns_basic_success(self):
        """Test basic APNS channel listing functionality."""
        device_id = "0000000000000000"

        envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        self.assertIsInstance(envelope.result.channels, list)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/gcm_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_gcm_basic_success(self):
        """Test basic GCM channel listing functionality."""
        device_id = "0000000000000000"

        envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.GCM) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        self.assertIsInstance(envelope.result.channels, list)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/apns2_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_apns2_basic_success(self):
        """Test basic APNS2 channel listing functionality."""
        device_id = "0000000000000000"
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        self.assertIsInstance(envelope.result.channels, list)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/mpns_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_mpns_basic_success(self):
        """Test basic MPNS channel listing functionality."""
        device_id = "0000000000000000"

        envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.MPNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        self.assertIsInstance(envelope.result.channels, list)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/empty_device.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_empty_device(self):
        """Test listing channels for device with no registered channels."""
        device_id = "0000000000000000"

        envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        self.assertIsInstance(envelope.result.channels, list)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/populated_device.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_populated_device(self):
        """Test listing channels for device with registered channels."""
        device_id = "0000000000000000"

        envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        self.assertIsInstance(envelope.result.channels, list)

    # ==============================================
    # END-TO-END WORKFLOW TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/after_add_operations.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_after_add_operations(self):
        """Test listing channels after adding channels to device."""
        device_id = "0000000000000000"
        channels_to_add = ["test_channel_1", "test_channel_2", "test_channel_3"]

        # First, add channels to the device
        add_envelope = self.pubnub.add_channels_to_push() \
            .channels(channels_to_add) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify add operation was successful
        self.assertIsNotNone(add_envelope)
        self.assertTrue(add_envelope.status.is_error() is False)

        # Now list the channels for the device
        list_envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify list operation was successful
        self.assertIsNotNone(list_envelope)
        self.assertIsNotNone(list_envelope.result)
        self.assertTrue(list_envelope.status.is_error() is False)
        self.assertIsInstance(list_envelope.result.channels, list)

        # Verify that the added channels are present in the list
        returned_channels = list_envelope.result.channels
        for channel in channels_to_add:
            self.assertIn(channel, returned_channels)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/after_remove_operations.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_after_remove_operations(self):
        """Test listing channels after removing channels from device."""
        device_id = "0000000000000000"
        initial_channels = ["channel_1", "channel_2", "channel_3", "channel_4"]
        channels_to_remove = ["channel_2", "channel_4"]

        # First, add channels to the device
        add_envelope = self.pubnub.add_channels_to_push() \
            .channels(initial_channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify add operation was successful
        self.assertIsNotNone(add_envelope)
        self.assertTrue(add_envelope.status.is_error() is False)

        # Remove some channels from the device
        remove_envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels_to_remove) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify remove operation was successful
        self.assertIsNotNone(remove_envelope)
        self.assertTrue(remove_envelope.status.is_error() is False)

        # Now list the channels for the device
        list_envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify list operation was successful
        self.assertIsNotNone(list_envelope)
        self.assertIsNotNone(list_envelope.result)
        self.assertTrue(list_envelope.status.is_error() is False)
        self.assertIsInstance(list_envelope.result.channels, list)

        # Verify that removed channels are not in the list
        returned_channels = list_envelope.result.channels
        for channel in channels_to_remove:
            self.assertNotIn(channel, returned_channels)

        # Verify that remaining channels are still present
        remaining_channels = [ch for ch in initial_channels if ch not in channels_to_remove]
        for channel in remaining_channels:
            self.assertIn(channel, returned_channels)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/after_mixed_operations.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_after_mixed_operations(self):
        """Test listing channels after various add/remove operations."""
        device_id = "0000000000000000"

        # Step 1: Add initial set of channels
        initial_channels = ["ch_1", "ch_2", "ch_3"]
        add_envelope_1 = self.pubnub.add_channels_to_push() \
            .channels(initial_channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()
        self.assertTrue(add_envelope_1.status.is_error() is False)

        # Step 2: Remove some channels
        channels_to_remove = ["ch_2"]
        remove_envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels_to_remove) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()
        self.assertTrue(remove_envelope.status.is_error() is False)

        # Step 3: Add more channels
        additional_channels = ["ch_4", "ch_5"]
        add_envelope_2 = self.pubnub.add_channels_to_push() \
            .channels(additional_channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()
        self.assertTrue(add_envelope_2.status.is_error() is False)

        # Step 4: Remove another channel
        more_channels_to_remove = ["ch_1"]
        remove_envelope_2 = self.pubnub.remove_channels_from_push() \
            .channels(more_channels_to_remove) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()
        self.assertTrue(remove_envelope_2.status.is_error() is False)

        # Final step: List channels and verify the final state
        list_envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify list operation was successful
        self.assertIsNotNone(list_envelope)
        self.assertIsNotNone(list_envelope.result)
        self.assertTrue(list_envelope.status.is_error() is False)
        self.assertIsInstance(list_envelope.result.channels, list)

        # Expected final channels: ch_3, ch_4, ch_5 (removed ch_1 and ch_2)
        expected_channels = ["ch_3", "ch_4", "ch_5"]
        removed_channels = ["ch_1", "ch_2"]

        returned_channels = list_envelope.result.channels

        # Verify expected channels are present
        for channel in expected_channels:
            self.assertIn(channel, returned_channels)

        # Verify removed channels are not present
        for channel in removed_channels:
            self.assertNotIn(channel, returned_channels)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/cross_device_isolation.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_cross_device_isolation(self):
        """Test that listing channels shows only device-specific channels."""
        device_id_1 = "0000000000000000"
        device_id_2 = "1111111111111111"

        device_1_channels = ["device1_ch1", "device1_ch2", "shared_channel"]
        device_2_channels = ["device2_ch1", "device2_ch2", "shared_channel"]

        # Add channels to device 1
        add_envelope_1 = self.pubnub.add_channels_to_push() \
            .channels(device_1_channels) \
            .device_id(device_id_1) \
            .push_type(PNPushType.APNS) \
            .sync()
        self.assertTrue(add_envelope_1.status.is_error() is False)

        # Add channels to device 2
        add_envelope_2 = self.pubnub.add_channels_to_push() \
            .channels(device_2_channels) \
            .device_id(device_id_2) \
            .push_type(PNPushType.APNS) \
            .sync()
        self.assertTrue(add_envelope_2.status.is_error() is False)

        # List channels for device 1
        list_envelope_1 = self.pubnub.list_push_channels() \
            .device_id(device_id_1) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify list operation was successful for device 1
        self.assertIsNotNone(list_envelope_1)
        self.assertIsNotNone(list_envelope_1.result)
        self.assertTrue(list_envelope_1.status.is_error() is False)
        self.assertIsInstance(list_envelope_1.result.channels, list)

        # List channels for device 2
        list_envelope_2 = self.pubnub.list_push_channels() \
            .device_id(device_id_2) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify list operation was successful for device 2
        self.assertIsNotNone(list_envelope_2)
        self.assertIsNotNone(list_envelope_2.result)
        self.assertTrue(list_envelope_2.status.is_error() is False)
        self.assertIsInstance(list_envelope_2.result.channels, list)

        # Verify device isolation - device 1 should only have its channels
        device_1_returned = list_envelope_1.result.channels
        for channel in device_1_channels:
            self.assertIn(channel, device_1_returned)

        # Device 1 should not have device 2 specific channels
        device_2_specific = ["device2_ch1", "device2_ch2"]
        for channel in device_2_specific:
            self.assertNotIn(channel, device_1_returned)

        # Verify device isolation - device 2 should only have its channels
        device_2_returned = list_envelope_2.result.channels
        for channel in device_2_channels:
            self.assertIn(channel, device_2_returned)

        # Device 2 should not have device 1 specific channels
        device_1_specific = ["device1_ch1", "device1_ch2"]
        for channel in device_1_specific:
            self.assertNotIn(channel, device_2_returned)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/after_device_removal.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_after_device_removal(self):
        """Test listing channels after device has been removed."""
        device_id = "0000000000000000"
        channels_to_add = ["channel_1", "channel_2", "channel_3"]

        # First, add channels to the device
        add_envelope = self.pubnub.add_channels_to_push() \
            .channels(channels_to_add) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify add operation was successful
        self.assertIsNotNone(add_envelope)
        self.assertTrue(add_envelope.status.is_error() is False)

        # Verify channels were added by listing them
        initial_list_envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(initial_list_envelope)
        self.assertTrue(initial_list_envelope.status.is_error() is False)
        initial_channels = initial_list_envelope.result.channels
        for channel in channels_to_add:
            self.assertIn(channel, initial_channels)

        # Remove the entire device from push notifications
        remove_device_envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify device removal was successful
        self.assertIsNotNone(remove_device_envelope)
        self.assertTrue(remove_device_envelope.status.is_error() is False)

        # Now list channels for the removed device
        final_list_envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Verify list operation was successful
        self.assertIsNotNone(final_list_envelope)
        self.assertIsNotNone(final_list_envelope.result)
        self.assertTrue(final_list_envelope.status.is_error() is False)
        self.assertIsInstance(final_list_envelope.result.channels, list)

        # Verify that the device has no channels registered (empty list)
        final_channels = final_list_envelope.result.channels
        self.assertEqual(len(final_channels), 0, "Device should have no channels after removal")

    # ==============================================
    # ERROR RESPONSE TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/missing_topic_apns2_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_missing_topic_apns2_error(self):
        """Test error response for APNS2 without required topic."""
        device_id = "0000000000000000"

        try:
            self.pubnub.list_push_channels() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .sync()
            self.fail("Expected PubNubException for missing topic")
        except PubNubException as e:
            assert "Push notification topic is missing. Required only if push type is APNS2." == str(e)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/invalid_push_type_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_invalid_push_type_error(self):
        """Test error response for invalid push type."""
        device_id = "0000000000000000"

        try:
            self.pubnub.list_push_channels() \
                .device_id(device_id) \
                .push_type("INVALID_PUSH_TYPE") \
                .sync()
            self.fail("Expected PubNubException for invalid push type")
        except PubNubException as e:
            assert 400 == e.get_status_code()
            assert "Invalid type argument" in e.get_error_message()

    # ==============================================
    # RESPONSE VALIDATION TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/success_response_structure.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_success_response_structure(self):
        """Test success response structure and content."""
        device_id = "0000000000000000"

        envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Validate envelope structure
        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertIsNotNone(envelope.status)

        # Validate status
        self.assertFalse(envelope.status.is_error())
        self.assertIsNotNone(envelope.status.status_code)
        self.assertEqual(envelope.status.status_code, 200)

        # Validate result structure
        self.assertIsInstance(envelope.result.channels, list)

    # ==============================================
    # APNS2 SPECIFIC TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/apns2_development_environment.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_apns2_development_environment(self):
        """Test APNS2 with development environment."""
        device_id = "0000000000000000"
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        self.assertIsInstance(envelope.result.channels, list)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/apns2_production_environment.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_apns2_production_environment(self):
        """Test APNS2 with production environment."""
        device_id = "0000000000000000"
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.PRODUCTION) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        self.assertIsInstance(envelope.result.channels, list)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/apns2_topic_validation.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_apns2_topic_validation(self):
        """Test APNS2 topic validation and format requirements."""
        device_id = "0000000000000000"

        # Test valid topic formats
        valid_topics = [
            "com.example.app",
            "com.example-app.notifications",
            "com.example_app.notifications",
            "com.EXAMPLE.APP.NOTIFICATIONS",
            "com.example.app.notifications-dev"
        ]

        for topic in valid_topics:
            envelope = self.pubnub.list_push_channels() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .topic(topic) \
                .environment(PNPushEnvironment.DEVELOPMENT) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)
            self.assertIsInstance(envelope.result.channels, list)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/list_push_channels/apns2_cross_environment_isolation.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_list_push_channels_apns2_cross_environment_isolation(self):
        """Test that channels are isolated between environments."""
        # TODO: Implement test for cross-environment isolation
        pass
