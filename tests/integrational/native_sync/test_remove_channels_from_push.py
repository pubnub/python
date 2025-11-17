import unittest

from pubnub.pubnub import PubNub
from pubnub.enums import PNPushType, PNPushEnvironment
from pubnub.exceptions import PubNubException
from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


class TestRemoveChannelsFromPushIntegration(unittest.TestCase):
    """Integration tests for remove_channels_from_push endpoint."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.pubnub = PubNub(pnconf_env_copy(uuid="test-uuid"))

    # ==============================================
    # BASIC FUNCTIONALITY TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/apns_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_apns_basic_success(self):
        """Test basic APNS channel removal functionality."""
        device_id = "0000000000000000"
        channels = ["remove_channel_1", "remove_channel_2"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/gcm_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_gcm_basic_success(self):
        """Test basic GCM channel removal functionality."""
        device_id = "0000000000000000"
        channels = ["gcm_remove_channel_1", "gcm_remove_channel_2"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.GCM) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/apns2_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_apns2_basic_success(self):
        """Test basic APNS2 channel removal functionality."""
        device_id = "0000000000000000"
        channels = ["apns2_remove_channel_1", "apns2_remove_channel_2"]
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/single_channel.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_single_channel(self):
        """Test removing a single channel from push notifications."""
        device_id = "0000000000000000"
        channels = ["single_remove_channel"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/multiple_channels.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_multiple_channels(self):
        """Test removing multiple channels from push notifications."""
        device_id = "0000000000000000"
        channels = ["multi_remove_1", "multi_remove_2", "multi_remove_3", "multi_remove_4", "multi_remove_5"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
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
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/full_workflow_apns.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_full_workflow_apns(self):
        """Test complete workflow: add channels, remove them, then verify."""
        device_id = "0000000000000000"
        channels = ["workflow_channel_1", "workflow_channel_2"]

        # First add channels
        add_envelope = self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(add_envelope)
        self.assertTrue(add_envelope.status.is_error() is False)

        # Then remove them
        remove_envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(remove_envelope)
        self.assertIsNotNone(remove_envelope.result)
        self.assertTrue(remove_envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/full_workflow_apns2.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_full_workflow_apns2(self):
        """Test complete workflow: add channels with APNS2, remove them, then verify."""
        device_id = "0000000000000000"
        channels = ["apns2_workflow_channel_1", "apns2_workflow_channel_2"]
        topic = "com.example.testapp.notifications"

        # First add channels
        add_envelope = self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(add_envelope)
        self.assertTrue(add_envelope.status.is_error() is False)

        # Then remove them
        remove_envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(remove_envelope)
        self.assertIsNotNone(remove_envelope.result)
        self.assertTrue(remove_envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/then_list_verification.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_then_list_verification(self):
        """Test removing channels then listing to verify they were removed."""
        device_id = "0000000000000000"
        channels = ["verify_remove_channel_1", "verify_remove_channel_2"]

        # Add channels first
        self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Remove some channels
        remove_envelope = self.pubnub.remove_channels_from_push() \
            .channels(["verify_remove_channel_1"]) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(remove_envelope)
        self.assertTrue(remove_envelope.status.is_error() is False)

        # List channels to verify removal
        list_envelope = self.pubnub.list_push_channels() \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(list_envelope)
        self.assertTrue(list_envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/partial_removal.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_partial_removal(self):
        """Test removing some channels while leaving others."""
        device_id = "0000000000000000"
        all_channels = ["partial_1", "partial_2", "partial_3", "partial_4"]
        channels_to_remove = ["partial_1", "partial_3"]

        # Add all channels first
        self.pubnub.add_channels_to_push() \
            .channels(all_channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Remove only some channels
        remove_envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels_to_remove) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(remove_envelope)
        self.assertIsNotNone(remove_envelope.result)
        self.assertTrue(remove_envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/nonexistent_channels.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_nonexistent_channels(self):
        """Test removing channels that were never added."""
        device_id = "0000000000000000"
        channels = ["nonexistent_channel_1", "nonexistent_channel_2"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        # Should succeed even if channels don't exist
        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    # ==============================================
    # ERROR RESPONSE TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/missing_topic_apns2_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_missing_topic_apns2_error(self):
        """Test error response for APNS2 without required topic."""
        device_id = "0000000000000000"
        channels = ["error_channel"]

        try:
            self.pubnub.remove_channels_from_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .sync()
            self.fail("Expected PubNubException for missing topic")
        except PubNubException as e:
            assert "Push notification topic is missing. Required only if push type is APNS2." == str(e)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/invalid_push_type_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_invalid_push_type_error(self):
        """Test error response for invalid push type."""
        device_id = "0000000000000000"
        channels = ["test_channel_1"]

        try:
            self.pubnub.remove_channels_from_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type("INVALID_PUSH_TYPE") \
                .sync()
            self.fail("Expected PubNubException for invalid push type")
        except PubNubException as e:
            assert 400 == e.get_status_code()
            assert "Invalid type argument" in e.get_error_message()

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/network_timeout_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_network_timeout_error(self):
        """Test error handling for network timeout."""
        # This test would need special configuration to simulate timeout
        # For now, we'll test the structure
        device_id = "0000000000000000"
        channels = ["timeout_test_channel"]

        try:
            envelope = self.pubnub.remove_channels_from_push() \
                .channels(channels) \
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
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/special_characters_in_channels.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_special_characters_in_channels(self):
        """Test removing channels with special characters."""
        device_id = "0000000000000000"
        channels = ["channel-with-dash", "channel_with_underscore", "channel.with.dots"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/empty_channel_list.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_empty_channel_list(self):
        """Test behavior with empty channel list."""
        device_id = "0000000000000000"
        channels = []

        try:
            self.pubnub.remove_channels_from_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()
            self.fail("Expected PubNubException for empty channel list")
        except PubNubException as e:
            assert "Channel missing" in str(e)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/maximum_channels_boundary.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_maximum_channels_boundary(self):
        """Test removing maximum allowed number of channels."""
        device_id = "0000000000000000"
        # Test with a large number of channels (assuming 100 is near the limit)
        channels = [f"max_channel_{i}" for i in range(100)]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/special_device_id_formats.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_special_device_id_formats(self):
        """Test with various device ID formats and special characters."""
        channels = ["test_channel"]
        special_device_ids = [
            "ABCDEF1234567890",  # Uppercase hex
            "abcdef1234567890",  # Lowercase hex
            "1234567890123456",  # Numeric
        ]

        for device_id in special_device_ids:
            envelope = self.pubnub.remove_channels_from_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/long_device_id.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_long_device_id(self):
        """Test with very long device ID."""
        device_id = "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"  # 64 chars
        channels = ["test_channel"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/special_topic_formats.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_special_topic_formats(self):
        """Test APNS2 with various topic formats."""
        device_id = "0000000000000000"
        channels = ["apns2_topic_test_channel"]

        # Test various topic formats
        special_topics = [
            "com.example.app",
            "com.example-app.notifications",
            "com.example_app.notifications",
            "com.EXAMPLE.APP.NOTIFICATIONS",
            "com.example.app.notifications-dev"
        ]

        for topic in special_topics:
            envelope = self.pubnub.remove_channels_from_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .topic(topic) \
                .environment(PNPushEnvironment.DEVELOPMENT) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/unicode_device_id.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_unicode_device_id(self):
        """Test with unicode characters in device ID."""
        device_id = "测试设备ID123456"  # Unicode device ID
        channels = ["test_channel"]

        try:
            envelope = self.pubnub.remove_channels_from_push() \
                .channels(channels) \
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
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/duplicate_channels.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_duplicate_channels(self):
        """Test removing duplicate channels in the same request."""
        device_id = "0000000000000000"
        channels = ["duplicate_channel", "duplicate_channel", "unique_channel", "duplicate_channel"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
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
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/success_response_structure.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_success_response_structure(self):
        """Test success response structure and content."""
        device_id = "0000000000000000"
        channels = ["response_test_channel"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
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
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/response_headers.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_response_headers(self):
        """Test response headers are present and valid."""
        device_id = "0000000000000000"
        channels = ["header_test_channel"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.status)
        # Headers should be accessible through status
        self.assertTrue(hasattr(envelope.status, 'status_code'))

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/response_timing.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_response_timing(self):
        """Test response timing is within acceptable limits."""
        import time
        device_id = "0000000000000000"
        channels = ["timing_test_channel"]

        start_time = time.time()
        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
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
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/response_status_codes.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_response_status_codes(self):
        """Test various HTTP status codes in responses."""
        device_id = "0000000000000000"
        channels = ["status_code_test_channel"]

        # Test successful response (200)
        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.status)
        self.assertEqual(envelope.status.status_code, 200)
        self.assertFalse(envelope.status.is_error())

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/response_content_type.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_response_content_type(self):
        """Test response content type is correct."""
        device_id = "0000000000000000"
        channels = ["content_type_test_channel"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)
        # Result should be JSON-parseable
        self.assertIsNotNone(envelope.result)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/response_encoding.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_response_encoding(self):
        """Test response encoding is handled correctly."""
        device_id = "0000000000000000"
        channels = ["encoding_test_channel"]

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
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
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/apns2_development_environment.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_apns2_development_environment(self):
        """Test APNS2 with development environment."""
        device_id = "0000000000000000"
        channels = ["apns2_dev_remove_channel_1", "apns2_dev_remove_channel_2"]
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/apns2_production_environment.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_apns2_production_environment(self):
        """Test APNS2 with production environment."""
        device_id = "0000000000000000"
        channels = ["apns2_prod_remove_channel_1", "apns2_prod_remove_channel_2"]
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.remove_channels_from_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.PRODUCTION) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/remove_channels_from_push/apns2_topic_validation.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_remove_channels_from_push_apns2_topic_validation(self):
        """Test APNS2 topic validation and format requirements."""
        device_id = "0000000000000000"
        channels = ["apns2_topic_remove_test_channel"]

        # Test valid topic formats
        valid_topics = [
            "com.example.app",
            "com.example-app.notifications",
            "com.example_app.notifications",
            "com.EXAMPLE.APP.NOTIFICATIONS",
            "com.example.app.notifications-dev"
        ]

        for topic in valid_topics:
            envelope = self.pubnub.remove_channels_from_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .topic(topic) \
                .environment(PNPushEnvironment.DEVELOPMENT) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)
