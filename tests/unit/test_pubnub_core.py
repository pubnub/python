import unittest
import os
from unittest.mock import patch, Mock

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.request_handlers.base import BaseRequestHandler
from pubnub.request_handlers.httpx import HttpxRequestHandler
from tests.helper import pnconf_copy


class MockCustomRequestHandler(BaseRequestHandler):
    """Mock custom request handler for testing purposes."""

    def __init__(self, pubnub_instance):
        super().__init__()
        self.pubnub_instance = pubnub_instance

    def sync_request(self, platform_options, endpoint_call_options):
        return Mock()

    def threaded_request(self, endpoint_name, platform_options, endpoint_call_options, callback, cancellation_event):
        return Mock()

    async def async_request(self, options_func, cancellation_event):
        return Mock()


class InvalidRequestHandler:
    """Invalid request handler that doesn't inherit from BaseRequestHandler."""

    def __init__(self, pubnub_instance):
        self.pubnub_instance = pubnub_instance


class TestPubNubCoreInit(unittest.TestCase):
    """Test suite for PubNub class initialization functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = pnconf_copy()

    def tearDown(self):
        """Clean up after tests."""
        # Clean up any environment variables set during tests
        if 'PUBNUB_REQUEST_HANDLER' in os.environ:
            del os.environ['PUBNUB_REQUEST_HANDLER']

    def test_basic_initialization(self):
        """Test basic PubNub initialization without custom request handler."""
        pubnub = PubNub(self.config)

        # Verify basic attributes are set
        self.assertIsInstance(pubnub.config, PNConfiguration)
        self.assertIsNotNone(pubnub._request_handler)
        self.assertIsInstance(pubnub._request_handler, HttpxRequestHandler)
        self.assertIsNotNone(pubnub._publish_sequence_manager)
        self.assertIsNotNone(pubnub._telemetry_manager)

        # Verify subscription manager is created when enabled
        if self.config.enable_subscribe:
            self.assertIsNotNone(pubnub._subscription_manager)

    def test_init_with_custom_request_handler_parameter(self):
        """Test initialization with custom request handler passed as parameter."""
        pubnub = PubNub(self.config, custom_request_handler=MockCustomRequestHandler)

        self.assertIsInstance(pubnub._request_handler, MockCustomRequestHandler)
        self.assertEqual(pubnub._request_handler.pubnub_instance, pubnub)

    def test_init_with_invalid_custom_request_handler_parameter(self):
        """Test initialization with invalid custom request handler raises exception."""
        with self.assertRaises(Exception) as context:
            PubNub(self.config, custom_request_handler=InvalidRequestHandler)

        self.assertIn("Custom request handler must be subclass of BaseRequestHandler", str(context.exception))

    @patch.dict(os.environ, {'PUBNUB_REQUEST_HANDLER': 'tests.unit.test_pubnub_core.MockCustomRequestHandler'})
    @patch('importlib.import_module')
    def test_init_with_env_var_request_handler(self, mock_import):
        """Test initialization with request handler specified via environment variable."""
        # Mock the module import
        mock_module = Mock()
        mock_module.MockCustomRequestHandler = MockCustomRequestHandler
        mock_import.return_value = mock_module

        pubnub = PubNub(self.config)

        # Verify the environment variable handler was loaded
        mock_import.assert_called_once_with('tests.unit.test_pubnub_core')
        self.assertIsInstance(pubnub._request_handler, MockCustomRequestHandler)

    @patch.dict(os.environ, {'PUBNUB_REQUEST_HANDLER': 'tests.unit.test_pubnub_core.InvalidRequestHandler'})
    @patch('importlib.import_module')
    def test_init_with_invalid_env_var_request_handler(self, mock_import):
        """Test initialization with invalid request handler from environment variable raises exception."""
        # Mock the module import
        mock_module = Mock()
        mock_module.InvalidRequestHandler = InvalidRequestHandler
        mock_import.return_value = mock_module

        with self.assertRaises(Exception) as context:
            PubNub(self.config)

        self.assertIn("Custom request handler must be subclass of BaseRequestHandler", str(context.exception))

    @patch.dict(os.environ, {'PUBNUB_REQUEST_HANDLER': 'nonexistent.module.Handler'})
    def test_init_with_nonexistent_env_var_module(self):
        """Test initialization with nonexistent module in environment variable."""
        with self.assertRaises(ModuleNotFoundError):
            PubNub(self.config)

    @patch.dict(os.environ, {'PUBNUB_REQUEST_HANDLER': 'tests.unit.test_pubnub_core.NonexistentHandler'})
    @patch('importlib.import_module')
    def test_init_with_nonexistent_env_var_class(self, mock_import):
        """Test initialization with nonexistent class in environment variable."""
        # Mock the module import but without the requested class
        mock_module = Mock()
        del mock_module.NonexistentHandler  # Ensure the attribute doesn't exist
        mock_import.return_value = mock_module

        with self.assertRaises(AttributeError):
            PubNub(self.config)

    def test_init_parameter_takes_precedence_over_env_var(self):
        """Test that custom_request_handler parameter takes precedence over environment variable."""
        with patch.dict(os.environ, {'PUBNUB_REQUEST_HANDLER': 'some.module.Handler'}):
            pubnub = PubNub(self.config, custom_request_handler=MockCustomRequestHandler)

            # Parameter should take precedence, so we should have MockCustomRequestHandler
            self.assertIsInstance(pubnub._request_handler, MockCustomRequestHandler)

    def test_init_with_subscription_disabled(self):
        """Test initialization when subscription is disabled."""
        self.config.enable_subscribe = False
        pubnub = PubNub(self.config)

        # Should not have subscription manager when disabled
        self.assertFalse(hasattr(pubnub, '_subscription_manager') and pubnub._subscription_manager is not None)

    def test_config_assertion(self):
        """Test that initialization raises AssertionError with invalid config type."""
        with self.assertRaises(AssertionError):
            PubNub("invalid_config_type")

        with self.assertRaises(AssertionError):
            PubNub(None)


class TestPubNubCoreMethods(unittest.TestCase):
    """Test suite for PubNub class core methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = pnconf_copy()
        self.pubnub = PubNub(self.config)

    def test_sdk_platform_returns_empty_string(self):
        """Test that sdk_platform method returns empty string."""
        result = self.pubnub.sdk_platform()
        self.assertEqual(result, "")
        self.assertIsInstance(result, str)

    def test_get_request_handler(self):
        """Test get_request_handler method returns current handler."""
        handler = self.pubnub.get_request_handler()

        self.assertIsNotNone(handler)
        self.assertIsInstance(handler, BaseRequestHandler)
        self.assertEqual(handler, self.pubnub._request_handler)

    def test_set_request_handler_valid(self):
        """Test set_request_handler with valid handler."""
        custom_handler = MockCustomRequestHandler(self.pubnub)

        self.pubnub.set_request_handler(custom_handler)

        self.assertEqual(self.pubnub._request_handler, custom_handler)
        self.assertEqual(self.pubnub.get_request_handler(), custom_handler)

    def test_set_request_handler_invalid_type(self):
        """Test set_request_handler with invalid handler type raises AssertionError."""
        invalid_handler = "not_a_handler"

        with self.assertRaises(AssertionError):
            self.pubnub.set_request_handler(invalid_handler)

    def test_set_request_handler_invalid_instance(self):
        """Test set_request_handler with object not inheriting from BaseRequestHandler."""
        invalid_handler = InvalidRequestHandler(self.pubnub)

        with self.assertRaises(AssertionError):
            self.pubnub.set_request_handler(invalid_handler)

    def test_set_request_handler_none(self):
        """Test set_request_handler with None raises AssertionError."""
        with self.assertRaises(AssertionError):
            self.pubnub.set_request_handler(None)

    def test_request_handler_persistence(self):
        """Test that request handler changes persist."""
        original_handler = self.pubnub.get_request_handler()
        custom_handler = MockCustomRequestHandler(self.pubnub)

        # Set new handler
        self.pubnub.set_request_handler(custom_handler)
        self.assertEqual(self.pubnub.get_request_handler(), custom_handler)

        # Set back to original
        self.pubnub.set_request_handler(original_handler)
        self.assertEqual(self.pubnub.get_request_handler(), original_handler)


class TestPubNubCoreInitManagers(unittest.TestCase):
    """Test suite for verifying proper initialization of internal managers."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = pnconf_copy()

    def test_publish_sequence_manager_initialization(self):
        """Test that publish sequence manager is properly initialized."""
        pubnub = PubNub(self.config)

        self.assertIsNotNone(pubnub._publish_sequence_manager)
        # Verify it has the expected max sequence
        self.assertEqual(pubnub._publish_sequence_manager.max_sequence, PubNub.MAX_SEQUENCE)

    def test_telemetry_manager_initialization(self):
        """Test that telemetry manager is properly initialized."""
        pubnub = PubNub(self.config)

        self.assertIsNotNone(pubnub._telemetry_manager)
        # Verify it's the native implementation
        from pubnub.pubnub import NativeTelemetryManager
        self.assertIsInstance(pubnub._telemetry_manager, NativeTelemetryManager)

    def test_subscription_manager_initialization_when_enabled(self):
        """Test subscription manager initialization when enabled."""
        self.config.enable_subscribe = True
        pubnub = PubNub(self.config)

        self.assertIsNotNone(pubnub._subscription_manager)
        from pubnub.pubnub import NativeSubscriptionManager
        self.assertIsInstance(pubnub._subscription_manager, NativeSubscriptionManager)

    def test_subscription_manager_not_initialized_when_disabled(self):
        """Test subscription manager is not initialized when disabled."""
        self.config.enable_subscribe = False
        pubnub = PubNub(self.config)

        # Should not have subscription manager attribute or it should be None
        if hasattr(pubnub, '_subscription_manager'):
            self.assertIsNone(pubnub._subscription_manager)


class TestPubNubCoreRequestHandlerEdgeCases(unittest.TestCase):
    """Test suite for edge cases in request handler handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = pnconf_copy()

    def tearDown(self):
        """Clean up after tests."""
        if 'PUBNUB_REQUEST_HANDLER' in os.environ:
            del os.environ['PUBNUB_REQUEST_HANDLER']

    @patch.dict(os.environ, {'PUBNUB_REQUEST_HANDLER': 'malformed_module_path'})
    def test_malformed_env_var_module_path(self):
        """Test handling of malformed module path in environment variable."""
        with self.assertRaises((ModuleNotFoundError, ValueError)):
            PubNub(self.config)

    @patch.dict(os.environ, {'PUBNUB_REQUEST_HANDLER': ''})
    def test_empty_env_var(self):
        """Test handling of empty environment variable."""
        # Empty env var should be ignored, default handler should be used
        pubnub = PubNub(self.config)
        self.assertIsInstance(pubnub._request_handler, HttpxRequestHandler)

    def test_multiple_custom_handler_operations(self):
        """Test multiple operations with custom request handlers."""
        pubnub = PubNub(self.config)

        # Start with default handler
        original_handler = pubnub.get_request_handler()
        self.assertIsInstance(original_handler, HttpxRequestHandler)

        # Switch to custom handler
        custom_handler1 = MockCustomRequestHandler(pubnub)
        pubnub.set_request_handler(custom_handler1)
        self.assertEqual(pubnub.get_request_handler(), custom_handler1)

        # Switch to another custom handler
        custom_handler2 = MockCustomRequestHandler(pubnub)
        pubnub.set_request_handler(custom_handler2)
        self.assertEqual(pubnub.get_request_handler(), custom_handler2)
        self.assertNotEqual(pubnub.get_request_handler(), custom_handler1)

        # Switch back to original
        pubnub.set_request_handler(original_handler)
        self.assertEqual(pubnub.get_request_handler(), original_handler)

    @patch.dict(os.environ, {'PUBNUB_REQUEST_HANDLER': 'tests.unit.test_pubnub_core.MockCustomRequestHandler'})
    def test_env_var_real_importlib_usage(self):
        """Test environment variable with real importlib module loading."""
        # This test uses the real importlib.import_module functionality
        pubnub = PubNub(self.config)

        # Since the MockCustomRequestHandler is defined in this module,
        # importlib should be able to load it
        self.assertIsInstance(pubnub._request_handler, MockCustomRequestHandler)


class TestPubNubCoreStopMethod(unittest.TestCase):
    """Test suite for PubNub stop method functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = pnconf_copy()

    def test_stop_with_subscription_manager_enabled(self):
        """Test stop method when subscription manager is enabled."""
        self.config.enable_subscribe = True
        pubnub = PubNub(self.config)

        # Should not raise exception
        try:
            pubnub.stop()
        except Exception as e:
            self.fail(f"stop() should not raise exception when subscription manager is enabled: {e}")

    def test_stop_with_subscription_manager_disabled(self):
        """Test stop method when subscription manager is disabled raises exception."""
        self.config.enable_subscribe = False
        pubnub = PubNub(self.config)

        with self.assertRaises(Exception) as context:
            pubnub.stop()

        self.assertIn("Subscription manager is not enabled for this instance", str(context.exception))
