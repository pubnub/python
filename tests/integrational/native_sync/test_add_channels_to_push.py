import unittest

from pubnub.pubnub import PubNub
from pubnub.enums import PNPushType, PNPushEnvironment
from pubnub.exceptions import PubNubException
from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


class TestAddChannelsToPushIntegration(unittest.TestCase):
    """Integration tests for add_channels_to_push endpoint."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.pubnub = PubNub(pnconf_env_copy(uuid="test-uuid"))

        # ==============================================
    # BASIC FUNCTIONALITY TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/apns_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_apns_basic_success(self):
        """Test basic APNS channel addition functionality."""
        device_id = "0000000000000000"
        channels = ["test_channel_1", "test_channel_2"]

        envelope = self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/gcm_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_gcm_basic_success(self):
        """Test basic GCM channel addition functionality."""
        device_id = "0000000000000000"
        channels = ["gcm_channel_1", "gcm_channel_2"]

        envelope = self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.GCM) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/apns2_basic_success.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_apns2_basic_success(self):
        """Test basic APNS2 channel addition functionality."""
        device_id = "0000000000000000"
        channels = ["apns2_channel_1", "apns2_channel_2"]
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS2) \
            .topic(topic) \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    # ==============================================
    # ERROR RESPONSE TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/invalid_device_id_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_invalid_device_id_error(self):
        """Test error response for invalid device ID."""
        device_id = "device_id_should_be_16_characters_long"
        channels = ["test_channel_1", "test_channel_2"]

        try:
            self.pubnub.add_channels_to_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()
            self.fail("Expected PubNubException for invalid device ID")
        except PubNubException as e:
            assert 400 == e.get_status_code()
            assert "Invalid device token" == e.get_error_message()

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/missing_topic_apns2_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_missing_topic_apns2_error(self):
        """Test error response for APNS2 without required topic."""
        device_id = "0000000000000000"
        channels = ["error_channel"]

        try:
            self.pubnub.add_channels_to_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .sync()
            self.fail("Expected PubNubException for invalid device ID")
        except PubNubException as e:
            assert "Push notification topic is missing. Required only if push type is APNS2." == str(e)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/invalid_push_type_error.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_invalid_push_type_error(self):
        """Test error response for invalid push type."""
        device_id = "0000000000000000"
        channels = ["test_channel_1"]

        try:
            self.pubnub.add_channels_to_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type("INVALID_PUSH_TYPE") \
                .sync()
            self.fail("Expected PubNubException for invalid push type")
        except PubNubException as e:
            assert 400 == e.get_status_code()
            assert "Invalid type argument" in e.get_error_message()

    # ==============================================
    # EDGE CASE TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/special_characters_in_channels.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_special_characters_in_channels(self):
        """Test adding channels with special characters."""
        device_id = "0000000000000000"
        channels = ["channel-with-dash", "channel_with_underscore", "channel.with.dots"]

        envelope = self.pubnub.add_channels_to_push() \
            .channels(channels) \
            .device_id(device_id) \
            .push_type(PNPushType.APNS) \
            .sync()

        self.assertIsNotNone(envelope)
        self.assertIsNotNone(envelope.result)
        self.assertTrue(envelope.status.is_error() is False)

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/empty_channel_list.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_empty_channel_list(self):
        """Test behavior with empty channel list."""
        device_id = "0000000000000000"
        channels = []

        try:
            self.pubnub.add_channels_to_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type(PNPushType.APNS) \
                .sync()
            self.fail("Expected PubNubException for empty channel list")
        except PubNubException as e:
            assert "Channel missing" in str(e)

    # ==============================================
    # RESPONSE VALIDATION TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/success_response_structure.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_success_response_structure(self):
        """Test success response structure and content."""
        device_id = "0000000000000000"
        channels = ["response_test_channel"]

        envelope = self.pubnub.add_channels_to_push() \
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
        'tests/integrational/fixtures/native_sync/add_channels_to_push/error_response_structure.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_error_response_structure(self):
        """Test error response structure and content."""
        # TODO: Implement test for error response validation
        pass

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/response_status_codes.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_response_status_codes(self):
        """Test various HTTP status codes in responses."""
        # TODO: Implement test for status code validation
        pass

    # ==============================================
    # APNS2 SPECIFIC TESTS
    # ==============================================

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/add_channels_to_push/apns2_development_environment.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_apns2_development_environment(self):
        """Test APNS2 with development environment."""
        device_id = "0000000000000000"
        channels = ["apns2_dev_channel_1", "apns2_dev_channel_2"]
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.add_channels_to_push() \
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
        'tests/integrational/fixtures/native_sync/add_channels_to_push/apns2_production_environment.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_apns2_production_environment(self):
        """Test APNS2 with production environment."""
        device_id = "0000000000000000"
        channels = ["apns2_prod_channel_1", "apns2_prod_channel_2"]
        topic = "com.example.testapp.notifications"

        envelope = self.pubnub.add_channels_to_push() \
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
        'tests/integrational/fixtures/native_sync/add_channels_to_push/apns2_topic_validation.json',
        serializer='pn_json',
        filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
    )
    def test_add_channels_to_push_apns2_topic_validation(self):
        """Test APNS2 topic validation and format requirements."""
        device_id = "0000000000000000"
        channels = ["apns2_topic_test_channel"]

        # Test valid topic formats
        valid_topics = [
            "com.example.app",
            "com.example-app.notifications",
            "com.example_app.notifications",
            "com.EXAMPLE.APP.NOTIFICATIONS",
            "com.example.app.notifications-dev"
        ]

        for topic in valid_topics:
            envelope = self.pubnub.add_channels_to_push() \
                .channels(channels) \
                .device_id(device_id) \
                .push_type(PNPushType.APNS2) \
                .topic(topic) \
                .environment(PNPushEnvironment.DEVELOPMENT) \
                .sync()

            self.assertIsNotNone(envelope)
            self.assertIsNotNone(envelope.result)
            self.assertTrue(envelope.status.is_error() is False)
