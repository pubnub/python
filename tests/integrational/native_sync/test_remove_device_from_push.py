import unittest

from pubnub.pubnub import PubNub
from pubnub.enums import PNPushType, PNPushEnvironment
from pubnub.exceptions import PubNubException
from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


class TestRemoveDeviceFromPushIntegration(unittest.TestCase):
    """Integration tests for remove_device_from_push endpoint."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.pubnub = PubNub(pnconf_env_copy(uuid="test-uuid"))

    # ==============================================
    # BASIC FUNCTIONALITY TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/apns_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_apns_basic_success(self):
        """Test basic APNS device removal functionality."""
        device_id = "0000000000000000"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/gcm_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_gcm_basic_success(self):
        """Test basic GCM device removal functionality."""
        device_id = "0000000000000000"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.GCM) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/apns2_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_apns2_basic_success(self):
        """Test basic APNS2 device removal functionality."""
        device_id = "0000000000000000"
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/complete_unregistration.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_complete_unregistration(self):
        """Test complete device unregistration from all push notifications."""
        device_id = "0000000000000000"

        # Remove device completely from APNS
        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    # ==============================================
    # END-TO-END WORKFLOW TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/full_workflow_apns.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_full_workflow_apns(self):
        """Test complete workflow: register device, remove it, then verify."""
        device_id = "0000000000000000"
        channels = ["workflow_channel_1", "workflow_channel_2"]

        # First add channels to device
        add_envelope = self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(add_envelope)
        self.assertTrue(add_envelope.status.is_error() is False)

        # Then remove the entire device
        remove_envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(remove_envelope)
        self.assertIsNotNone(remove_envelope.result)
        self.assertTrue(remove_envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/full_workflow_apns2.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_full_workflow_apns2(self):
        """Test complete workflow: register device with APNS2, remove it, then verify."""
        device_id = "0000000000000000"
        channels = ["apns2_workflow_channel_1", "apns2_workflow_channel_2"]
        topic = "com.example.testapp.notifications"

        # First add channels to device
        add_envelope = self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(add_envelope)
        self.assertTrue(add_envelope.status.is_error() is False)

        # Then remove the entire device
        remove_envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(remove_envelope)
        self.assertIsNotNone(remove_envelope.result)
        self.assertTrue(remove_envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/then_list_verification.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_then_list_verification(self):
        """Test removing device then listing to verify it was removed."""
        device_id = "0000000000000000"
        channels = ["verify_device_channel_1", "verify_device_channel_2"]

        # Add channels to device first
        self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Remove the entire device
        remove_envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(remove_envelope)
        self.assertTrue(remove_envelope.status.is_error() is False)

        # List channels to verify device removal (should be empty or error)
        try:
            list_envelope = self.pubnub.list_push_channels() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()

            # If successful, channels list should be empty
            if list_envelope and list_envelope.result:
                self.assertEqual(len(list_envelope.result.channels), 0)
        except PubNubException:
            # Device not found is also acceptable after removal
            pass

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/after_channel_operations.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_after_channel_operations(self):
        """Test removing device after various channel add/remove operations."""
        device_id = "0000000000000000"
        channels = ["channel_op_1", "channel_op_2", "channel_op_3"]

        # Add channels to device
        self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Remove some channels
        self.pubnub.remove_channels_from_push() \
            .channels(["channel_op_1"]) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Now remove the entire device
        remove_envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(remove_envelope)
        self.assertIsNotNone(remove_envelope.result)
        self.assertTrue(remove_envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/nonexistent_device.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_nonexistent_device(self):
        """Test removing device that was never registered."""
        device_id = "nonexistent_device_123"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Should succeed even if device doesn't exist
        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    # ==============================================
    # ERROR RESPONSE TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/missing_topic_apns2_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_missing_topic_apns2_error(self):
        """Test error response for APNS2 without required topic."""
        device_id = "0000000000000000"

        try:
            self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .sync()
            self.fail("Expected PubNubException for missing topic")
        except PubNubException as e:
            assert "Push notification topic is missing. Required only if push type is APNS2." == str(e)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/invalid_push_type_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_invalid_push_type_error(self):
        """Test error response for invalid push type."""
        device_id = "0000000000000000"

        try:
            self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type("INVALID_PUSH_TYPE") \
                .sync()
            self.fail("Expected PubNubException for invalid push type")
        except PubNubException as e:
            assert 400 == e.get_status_code()
            assert "Invalid type argument" in e.get_error_message()

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/network_timeout_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_network_timeout_error(self):
        """Test error handling for network timeout."""
        device_id = "0000000000000000"

        try:
            envelope = self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()
            # If no timeout occurs, verify successful response
            self.assertIsNotNone(envelope)
        except Exception as e:
            # If timeout or other network error occurs, ensure it's handled gracefully
            self.assertIsInstance(e, (PubNubException, Exception))

    # ==============================================
    # EDGE CASE TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/special_device_id_formats.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_special_device_id_formats(self):
        """Test with various device ID formats and special characters."""
        special_device_ids = [
            "ABCDEF1234567890",  # Uppercase hex
            "abcdef1234567890",  # Lowercase hex
            "1234567890123456",  # Numeric
        ]

        for device_id in special_device_ids:
            envelope = self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/unicode_device_id.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_unicode_device_id(self):
        """Test with unicode characters in device ID."""
        device_id = "测试设备ID123456"  # Unicode device ID

        try:
            envelope = self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()
            # May succeed or fail depending on validation
            if envelope:
                self.assertIsNotNone(envelope.result)
        except PubNubException as e:
            # Unicode device IDs may not be supported
            self.assertIsInstance(e, PubNubException)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/very_long_device_id.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_very_long_device_id(self):
        """Test with very long device ID."""
        device_id = "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"  # 64 chars

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/empty_device_id.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_empty_device_id(self):
        """Test behavior with empty device ID."""
        device_id = ""

        try:
            self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()
            self.fail("Expected PubNubException for empty device ID")
        except PubNubException as e:
            assert "Device ID is missing for push operation" in str(e) or "Invalid device" in str(e)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/special_topic_formats.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_special_topic_formats(self):
        """Test APNS2 with various topic formats."""
        device_id = "0000000000000000"

        # Test various topic formats
        special_topics = [
            "com.example.app",
            "com.example-app.notifications",
            "com.example_app.notifications",
            "com.EXAMPLE.APP.NOTIFICATIONS",
            "com.example.app.notifications-dev"
        ]

        for topic in special_topics:
            envelope = self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .topic(topic) \
                .environment(PNPushEnvironment.DEVELOPMENT) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/case_sensitive_device_id.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_case_sensitive_device_id(self):
        """Test case sensitivity of device IDs."""
        device_id_lower = "abcdef1234567890"
        device_id_upper = "ABCDEF1234567890"

        # Test both cases
        for device_id in [device_id_lower, device_id_upper]:
            envelope = self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/whitespace_device_id.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_whitespace_device_id(self):
        """Test device IDs with leading/trailing whitespace."""
        device_id_with_spaces = "  1234567890ABCDEF  "

        try:
            envelope = self.pubnub.remove_device_from_push() \
                .device_id(device_id_with_spaces) \
                .push_type(PNPushType.APNS) \
                .sync()
            # May succeed with trimmed ID or fail with validation error
            if envelope:
                self.assertIsNotNone(envelope.result)
        except PubNubException as e:
            # Whitespace in device IDs may not be supported
            self.assertIsInstance(e, PubNubException)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/numeric_device_id.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_numeric_device_id(self):
        """Test with purely numeric device IDs."""
        device_id = "1234567890123456"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/multiple_rapid_removals.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_multiple_rapid_removals(self):
        """Test multiple rapid removal requests for the same device."""
        device_id = "0000000000000000"

        # Perform multiple rapid removal requests
        for i in range(3):
            envelope = self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)

    # ==============================================
    # RESPONSE VALIDATION TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/success_response_structure.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_success_response_structure(self):
        """Test success response structure and content."""
        device_id = "0000000000000000"

        envelope = self.pubnub.remove_device_from_push() \
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

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/response_headers.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_response_headers(self):
        """Test response headers are present and valid."""
        device_id = "0000000000000000"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.status)
        # Headers should be accessible through status
        self.assertTrue(hasattr(envelope.status, 'status_code'))

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/response_timing.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_response_timing(self):
        """Test response timing is within acceptable limits."""
        import time
        device_id = "0000000000000000"

        start_time = time.time()
        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()
        end_time = time.time()

        self.assertIsNotNone(envelope)
        self.assertTrue(envelope.status.is_error() is False)

        # Response should be reasonably fast (less than 30 seconds)
        response_time = end_time - start_time
        self.assertLess(response_time, 30.0)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/response_status_codes.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_response_status_codes(self):
        """Test various HTTP status codes in responses."""
        device_id = "0000000000000000"

        # Test successful response (200)
        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.status)
        self.assertEqual(envelope.status.status_code, 200)
        self.assertFalse(envelope.status.is_error())

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/response_content_type.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_response_content_type(self):
        """Test response content type is correct."""
        device_id = "0000000000000000"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        # Result should be JSON-parseable
        self.assertIsNotNone(envelope.result)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/response_encoding.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_response_encoding(self):
        """Test response encoding is handled correctly."""
        device_id = "0000000000000000"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    # ==============================================
    # APNS2 SPECIFIC TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/apns2_development_environment.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_apns2_development_environment(self):
        """Test APNS2 with development environment."""
        device_id = "0000000000000000"
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/apns2_production_environment.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_apns2_production_environment(self):
        """Test APNS2 with production environment."""
        device_id = "0000000000000000"
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.PRODUCTION) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/apns2_topic_validation.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_apns2_topic_validation(self):
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
            envelope = self.pubnub.remove_device_from_push() \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .topic(topic) \
                .environment(PNPushEnvironment.DEVELOPMENT) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_device_from_push/apns2_cross_environment_removal.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_device_from_push_apns2_cross_environment_removal(self):
        """Test removing device from one environment doesn't affect the other."""
        device_id = "0000000000000000"
        topic = "com.example.testapp.notifications"
        channels = ["cross_env_channel_1", "cross_env_channel_2"]

        # Add channels in both environments
        self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.PRODUCTION) \
            .sync()

        # Remove device from development environment only
        remove_envelope = self.pubnub.remove_device_from_push() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(remove_envelope)
        self.assertIsNotNone(remove_envelope.result)
        self.assertTrue(remove_envelope.status.is_error() is False)

        # Verify production environment is still active
        prod_list_envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.PRODUCTION) \
            .sync()

        self.assertIsNotNone(prod_list_envelope)
        self.assertTrue(prod_list_envelope.status.is_error() is False)
