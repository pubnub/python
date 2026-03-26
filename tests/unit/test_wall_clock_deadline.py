"""Tests for wall-clock deadline detection in request handlers.

On macOS and Linux, time.monotonic() does not advance during system sleep,
causing socket timeouts (which use monotonic time) to take much longer than
expected in wall-clock time. These tests verify that the wall-clock deadline
mechanism detects this and cancels requests promptly.
"""
import asyncio
import threading
import time
import unittest
from unittest.mock import patch, MagicMock

import httpx

from pubnub.request_handlers.httpx import WallClockDeadlineWatchdog


class TestWallClockDeadlineWatchdog(unittest.TestCase):
    """Tests for the persistent per-thread WallClockDeadlineWatchdog."""

    def _make_watchdog(self, check_interval=0.1):
        watchdog = WallClockDeadlineWatchdog()
        watchdog.CHECK_INTERVAL = check_interval
        return watchdog

    def test_watchdog_does_not_trigger_before_deadline(self):
        """Watchdog should not trigger when deadline hasn't passed."""
        session = MagicMock(spec=httpx.Client)
        watchdog = self._make_watchdog()

        watchdog.set_deadline(session, time.time() + 60)
        time.sleep(0.3)
        watchdog.clear_deadline()
        watchdog.stop()

        self.assertFalse(watchdog.triggered)
        session.close.assert_not_called()

    def test_watchdog_triggers_when_deadline_passed(self):
        """Watchdog should trigger when wall-clock deadline has already passed."""
        session = MagicMock(spec=httpx.Client)
        watchdog = self._make_watchdog()

        watchdog.set_deadline(session, time.time() - 1)
        time.sleep(0.5)
        watchdog.stop()

        self.assertTrue(watchdog.triggered)
        session.close.assert_called_once()

    def test_watchdog_detects_simulated_sleep(self):
        """Simulate system sleep by making time.time() jump forward."""
        session = MagicMock(spec=httpx.Client)
        real_time = time.time

        start_wall = real_time()
        deadline = start_wall + 10

        call_count = [0]

        def mock_time():
            call_count[0] += 1
            if call_count[0] <= 2:
                return real_time()
            else:
                return start_wall + 60

        watchdog = self._make_watchdog()

        with patch('pubnub.request_handlers.httpx.time') as mock_time_module:
            mock_time_module.time = mock_time
            watchdog.set_deadline(session, deadline)
            time.sleep(0.5)

        watchdog.stop()

        self.assertTrue(watchdog.triggered)
        session.close.assert_called_once()

    def test_watchdog_reuse_across_requests(self):
        """Watchdog thread should be reused across multiple set/clear cycles."""
        session = MagicMock(spec=httpx.Client)
        watchdog = self._make_watchdog()

        # First request
        watchdog.set_deadline(session, time.time() + 60)
        time.sleep(0.05)
        thread_id_1 = watchdog._thread.ident
        watchdog.clear_deadline()

        # Second request
        watchdog.set_deadline(session, time.time() + 60)
        time.sleep(0.05)
        thread_id_2 = watchdog._thread.ident
        watchdog.clear_deadline()

        watchdog.stop()

        self.assertEqual(thread_id_1, thread_id_2)
        self.assertFalse(watchdog.triggered)

    def test_watchdog_resets_triggered_on_new_deadline(self):
        """set_deadline() should reset the triggered flag for the calling thread."""
        session = MagicMock(spec=httpx.Client)
        watchdog = self._make_watchdog()

        # Trigger the watchdog
        watchdog.set_deadline(session, time.time() - 1)
        time.sleep(0.3)
        self.assertTrue(watchdog.triggered)

        # New deadline resets triggered
        watchdog.set_deadline(session, time.time() + 60)
        self.assertFalse(watchdog.triggered)

        watchdog.clear_deadline()
        watchdog.stop()

    def test_watchdog_clear_prevents_trigger(self):
        """clear_deadline() before deadline passes should prevent triggering."""
        session = MagicMock(spec=httpx.Client)
        watchdog = self._make_watchdog(check_interval=0.5)

        watchdog.set_deadline(session, time.time() + 0.3)
        watchdog.clear_deadline()
        time.sleep(0.8)

        watchdog.stop()

        self.assertFalse(watchdog.triggered)
        session.close.assert_not_called()

    def test_watchdog_thread_is_daemon(self):
        """Watchdog thread must be daemon so it doesn't prevent process exit."""
        watchdog = self._make_watchdog()
        session = MagicMock(spec=httpx.Client)

        watchdog.set_deadline(session, time.time() + 300)
        self.assertTrue(watchdog._thread.daemon)

        watchdog.clear_deadline()
        watchdog.stop()

    def test_watchdog_handles_session_close_exception(self):
        """Watchdog should handle exceptions from session.close() gracefully."""
        session = MagicMock(spec=httpx.Client)
        session.close.side_effect = RuntimeError("Already closed")
        watchdog = self._make_watchdog()

        watchdog.set_deadline(session, time.time() - 1)
        time.sleep(0.5)
        watchdog.stop()

        self.assertTrue(watchdog.triggered)

    def test_watchdog_thread_exits_on_stop(self):
        """Watchdog thread should exit after stop() is called."""
        watchdog = self._make_watchdog()
        session = MagicMock(spec=httpx.Client)

        watchdog.set_deadline(session, time.time() + 300)
        time.sleep(0.05)
        watchdog.stop()
        time.sleep(0.3)

        self.assertFalse(watchdog._thread.is_alive())

    def test_watchdog_no_thread_until_needed(self):
        """Thread should not be created until set_deadline() is called."""
        watchdog = self._make_watchdog()
        self.assertIsNone(watchdog._thread)

        session = MagicMock(spec=httpx.Client)
        watchdog.set_deadline(session, time.time() + 60)
        self.assertIsNotNone(watchdog._thread)

        watchdog.clear_deadline()
        watchdog.stop()

    def test_concurrent_requests_independent_deadlines(self):
        """Deadlines from different threads should not interfere with each other."""
        session = MagicMock(spec=httpx.Client)
        watchdog = self._make_watchdog()

        thread1_triggered = [None]
        thread2_triggered = [None]

        def thread1_work():
            # Long deadline — should NOT trigger
            watchdog.set_deadline(session, time.time() + 60)
            time.sleep(0.5)
            thread1_triggered[0] = watchdog.triggered
            watchdog.clear_deadline()

        def thread2_work():
            # Already-passed deadline — SHOULD trigger
            time.sleep(0.05)  # Start slightly after thread1
            watchdog.set_deadline(session, time.time() - 1)
            time.sleep(0.4)
            thread2_triggered[0] = watchdog.triggered
            watchdog.clear_deadline()

        t1 = threading.Thread(target=thread1_work)
        t2 = threading.Thread(target=thread2_work)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        watchdog.stop()

        self.assertFalse(thread1_triggered[0], "Thread 1 (long deadline) should not be triggered")
        self.assertTrue(thread2_triggered[0], "Thread 2 (past deadline) should be triggered")

    def test_clear_from_one_thread_does_not_affect_another(self):
        """clear_deadline() from thread A should not clear thread B's deadline."""
        session = MagicMock(spec=httpx.Client)
        watchdog = self._make_watchdog()

        barrier = threading.Barrier(2)
        thread_b_triggered = [None]

        def thread_a():
            watchdog.set_deadline(session, time.time() + 60)
            barrier.wait()  # Sync with thread B
            watchdog.clear_deadline()

        def thread_b():
            watchdog.set_deadline(session, time.time() - 1)
            barrier.wait()  # Sync with thread A
            time.sleep(0.3)  # Wait for watchdog to process
            thread_b_triggered[0] = watchdog.triggered
            watchdog.clear_deadline()

        ta = threading.Thread(target=thread_a)
        tb = threading.Thread(target=thread_b)
        ta.start()
        tb.start()
        ta.join()
        tb.join()

        watchdog.stop()

        self.assertTrue(thread_b_triggered[0], "Thread B's expired deadline should still trigger")


class TestAsyncWallClockDeadline(unittest.TestCase):
    """Tests for the asyncio wall-clock deadline in AsyncHttpxRequestHandler."""

    def test_async_deadline_cancels_on_simulated_sleep(self):
        """Async request should be cancelled when wall-clock deadline passes."""
        from pubnub.request_handlers.async_httpx import AsyncHttpxRequestHandler

        handler = AsyncHttpxRequestHandler.__new__(AsyncHttpxRequestHandler)
        handler._session = MagicMock()

        async def never_completes(**kwargs):
            await asyncio.sleep(3600)

        handler._session.request = never_completes

        async def run_test():
            real_time = time.time
            start = real_time()
            call_count = [0]

            def mock_time():
                call_count[0] += 1
                if call_count[0] <= 3:
                    return real_time()
                return start + 60

            with patch('pubnub.request_handlers.async_httpx.time') as mock_time_module:
                mock_time_module.time = mock_time
                original = AsyncHttpxRequestHandler.WALL_CLOCK_CHECK_INTERVAL
                AsyncHttpxRequestHandler.WALL_CLOCK_CHECK_INTERVAL = 0.1
                try:
                    with self.assertRaises(asyncio.TimeoutError):
                        await handler._request_with_wall_clock_deadline(
                            {"method": "GET", "url": "http://test"},
                            timeout=10
                        )
                finally:
                    AsyncHttpxRequestHandler.WALL_CLOCK_CHECK_INTERVAL = original

        asyncio.run(run_test())

    def test_async_deadline_passes_through_normal_response(self):
        """Normal responses should pass through unaffected."""
        from pubnub.request_handlers.async_httpx import AsyncHttpxRequestHandler

        handler = AsyncHttpxRequestHandler.__new__(AsyncHttpxRequestHandler)
        handler._session = MagicMock()

        mock_response = MagicMock()

        async def quick_response(**kwargs):
            return mock_response

        handler._session.request = quick_response

        async def run_test():
            result = await handler._request_with_wall_clock_deadline(
                {"method": "GET", "url": "http://test"},
                timeout=10
            )
            self.assertEqual(result, mock_response)

        asyncio.run(run_test())

    def test_async_deadline_none_timeout_skips_watchdog(self):
        """When timeout is None, should call request directly without watchdog."""
        from pubnub.request_handlers.async_httpx import AsyncHttpxRequestHandler

        handler = AsyncHttpxRequestHandler.__new__(AsyncHttpxRequestHandler)
        handler._session = MagicMock()

        mock_response = MagicMock()

        async def quick_response(**kwargs):
            return mock_response

        handler._session.request = quick_response

        async def run_test():
            result = await handler._request_with_wall_clock_deadline(
                {"method": "GET", "url": "http://test"},
                timeout=None
            )
            self.assertEqual(result, mock_response)

        asyncio.run(run_test())

    def test_async_deadline_propagates_request_exception(self):
        """Exceptions from the HTTP request should propagate normally."""
        from pubnub.request_handlers.async_httpx import AsyncHttpxRequestHandler

        handler = AsyncHttpxRequestHandler.__new__(AsyncHttpxRequestHandler)
        handler._session = MagicMock()

        async def failing_request(**kwargs):
            raise httpx.ConnectError("Connection refused")

        handler._session.request = failing_request

        async def run_test():
            with self.assertRaises(httpx.ConnectError):
                await handler._request_with_wall_clock_deadline(
                    {"method": "GET", "url": "http://test"},
                    timeout=10
                )

        asyncio.run(run_test())


class TestHttpxRequestHandlerCleanup(unittest.TestCase):
    """Tests for proper cleanup of HttpxRequestHandler."""

    def test_close_stops_watchdog(self):
        """HttpxRequestHandler.close() should stop the watchdog thread."""
        from pubnub.request_handlers.httpx import HttpxRequestHandler

        handler = HttpxRequestHandler(MagicMock())
        session = handler._ensure_session()
        # Start the watchdog by setting a deadline
        handler._watchdog.set_deadline(session, time.time() + 300)
        self.assertIsNotNone(handler._watchdog._thread)

        handler.close()
        time.sleep(0.2)

        self.assertTrue(handler._watchdog._stop.is_set())


class TestHttpxSessionRecreation(unittest.TestCase):
    """Tests for automatic session recreation after watchdog closes the session.

    When the WallClockDeadlineWatchdog closes the httpx.Client during system sleep,
    subsequent requests (e.g., reconnection /time/0 calls) must detect the closed
    session and recreate it. Without this, native threads reconnection never succeeds.
    """

    def _make_handler(self):
        from pubnub.request_handlers.httpx import HttpxRequestHandler
        pubnub_mock = MagicMock()
        pubnub_mock.config.origin = 'ps.pndsn.com'
        pubnub_mock.config.scheme.return_value = 'https'
        handler = HttpxRequestHandler(pubnub_mock)
        return handler

    def test_closed_session_is_recreated_on_next_request(self):
        """After session.close(), the next _invoke_request should recreate the session."""
        handler = self._make_handler()
        original_session = handler._ensure_session()

        # Simulate what the watchdog does
        original_session.close()
        self.assertTrue(handler._session.is_closed)

        # Build minimal request options
        from pubnub.structures import RequestOptions, PlatformOptions
        p_options = MagicMock(spec=PlatformOptions)
        p_options.pn_config = MagicMock()
        p_options.pn_config.scheme.return_value = 'https'
        p_options.headers = {}

        e_options = MagicMock(spec=RequestOptions)
        e_options.method_string = 'GET'
        e_options.path = '/time/0'
        e_options.query_string = 'pnsdk=test'
        e_options.request_headers = None
        e_options.connect_timeout = 10
        e_options.request_timeout = 10
        e_options.is_post.return_value = False
        e_options.is_patch.return_value = False
        e_options.allow_redirects = True
        e_options.use_base_path = True

        # The request will fail (no real server), but session should be recreated first
        try:
            handler._invoke_request(p_options, e_options, 'ps.pndsn.com')
        except Exception:
            pass

        self.assertFalse(handler._session.is_closed)
        self.assertIsNot(handler._session, original_session)

        handler.close()

    def test_open_session_is_not_recreated(self):
        """An open session should not be replaced."""
        handler = self._make_handler()
        original_session = handler._ensure_session()

        self.assertFalse(handler._session.is_closed)

        from pubnub.structures import RequestOptions, PlatformOptions
        p_options = MagicMock(spec=PlatformOptions)
        p_options.pn_config = MagicMock()
        p_options.pn_config.scheme.return_value = 'https'
        p_options.headers = {}

        e_options = MagicMock(spec=RequestOptions)
        e_options.method_string = 'GET'
        e_options.path = '/time/0'
        e_options.query_string = 'pnsdk=test'
        e_options.request_headers = None
        e_options.connect_timeout = 10
        e_options.request_timeout = 10
        e_options.is_post.return_value = False
        e_options.is_patch.return_value = False
        e_options.allow_redirects = True
        e_options.use_base_path = True

        try:
            handler._invoke_request(p_options, e_options, 'ps.pndsn.com')
        except Exception:
            pass

        self.assertIs(handler._session, original_session)
        handler.close()

    def test_watchdog_trigger_with_timeout_exception_recreates_session(self):
        """When watchdog triggers and the request gets TimeoutException, session should be recreated."""
        handler = self._make_handler()
        original_session = handler._ensure_session()

        # Set up watchdog as triggered
        handler._watchdog.set_deadline(original_session, time.time() - 1)
        time.sleep(0.3)
        self.assertTrue(original_session.is_closed)

        from pubnub.structures import RequestOptions, PlatformOptions
        p_options = MagicMock(spec=PlatformOptions)
        p_options.pn_config = MagicMock()
        p_options.pn_config.scheme.return_value = 'https'
        p_options.headers = {}

        e_options = MagicMock(spec=RequestOptions)
        e_options.method_string = 'GET'
        e_options.path = '/v2/subscribe/demo/test/0'
        e_options.query_string = 'tt=0&pnsdk=test'
        e_options.request_headers = None
        e_options.connect_timeout = 10
        e_options.request_timeout = 310  # > 30, triggers watchdog usage
        e_options.is_post.return_value = False
        e_options.is_patch.return_value = False
        e_options.allow_redirects = True
        e_options.use_base_path = True

        try:
            handler._invoke_request(p_options, e_options, 'ps.pndsn.com')
        except Exception:
            pass

        # Session should have been recreated by _ensure_session() since original was closed
        self.assertFalse(handler._session.is_closed)
        self.assertIsNot(handler._session, original_session)

        handler._watchdog.stop()
        handler.close()

    def test_reconnection_time_request_works_after_session_close(self):
        """Simulates the reconnection manager's /time/0 call after watchdog closed the session.

        This is the exact scenario that caused native threads to never reconnect:
        1. Watchdog closes session during subscribe long-poll
        2. Reconnection manager starts making /time/0 calls
        3. /time/0 calls should detect closed session, recreate it, and eventually succeed
        """
        handler = self._make_handler()
        original_session = handler._ensure_session()

        # Step 1: Watchdog closes the session
        original_session.close()
        self.assertTrue(handler._session.is_closed)

        from pubnub.structures import RequestOptions, PlatformOptions
        p_options = MagicMock(spec=PlatformOptions)
        p_options.pn_config = MagicMock()
        p_options.pn_config.scheme.return_value = 'https'
        p_options.headers = {}

        # Step 2: /time/0 request (short timeout, no watchdog)
        e_options = MagicMock(spec=RequestOptions)
        e_options.method_string = 'GET'
        e_options.path = '/time/0'
        e_options.query_string = 'pnsdk=test'
        e_options.request_headers = None
        e_options.connect_timeout = 10
        e_options.request_timeout = 10  # Short timeout, use_watchdog=False
        e_options.is_post.return_value = False
        e_options.is_patch.return_value = False
        e_options.allow_redirects = True
        e_options.use_base_path = True

        # Step 3: The request may fail (no real server) but should NOT fail due to closed session
        try:
            handler._invoke_request(p_options, e_options, 'ps.pndsn.com')
        except Exception as e:
            # Should be a connection error, NOT "Cannot send a request, as the client has been closed"
            self.assertNotIn("client has been closed", str(e).lower())

        self.assertFalse(handler._session.is_closed)
        handler.close()


class TestWallClockErrorCategory(unittest.TestCase):
    """Tests that wall-clock sleep timeouts produce PNTimeoutCategory,
    so they silently restart the subscribe loop. If the network is actually
    down, the next request will fail with a real connection error that routes
    through the reconnection manager with configured retry delays.
    """

    def test_watchdog_triggered_produces_timeout_error(self):
        """When watchdog triggers during a request, the exception should use PNERR_CLIENT_TIMEOUT
        which maps to PNTimeoutCategory in _build_envelope."""
        from pubnub.request_handlers.httpx import HttpxRequestHandler
        from pubnub.errors import PNERR_CLIENT_TIMEOUT
        from pubnub.exceptions import PubNubException
        from pubnub.structures import RequestOptions, PlatformOptions

        handler = HttpxRequestHandler(MagicMock())

        # Simulate: session is open, but request fails with TimeoutException
        # while watchdog is in triggered state (watchdog fired DURING the request)
        mock_session = MagicMock(spec=httpx.Client)
        mock_session.is_closed = False
        mock_session.request.side_effect = httpx.ReadTimeout("timed out")
        handler._session = mock_session

        # Mock watchdog.triggered to return True (simulates watchdog firing during request)
        type(handler._watchdog).triggered = property(lambda self: True)

        p_options = MagicMock(spec=PlatformOptions)
        p_options.pn_config = MagicMock()
        p_options.pn_config.scheme.return_value = 'https'
        p_options.headers = {}

        e_options = MagicMock(spec=RequestOptions)
        e_options.method_string = 'GET'
        e_options.path = '/v2/subscribe/demo/test/0'
        e_options.query_string = 'tt=0&pnsdk=test'
        e_options.request_headers = None
        e_options.connect_timeout = 10
        e_options.request_timeout = 310  # > 30, so use_watchdog=True
        e_options.is_post.return_value = False
        e_options.is_patch.return_value = False
        e_options.allow_redirects = True
        e_options.use_base_path = True

        with self.assertRaises(PubNubException) as ctx:
            handler._invoke_request(p_options, e_options, 'ps.pndsn.com')

        self.assertEqual(ctx.exception._pn_error, PNERR_CLIENT_TIMEOUT)
        self.assertIn("Wall-clock deadline exceeded", ctx.exception._errormsg)

        handler._watchdog.stop()
        handler.close()

    def test_async_wall_clock_timeout_raises_wall_clock_error(self):
        """_request_with_wall_clock_deadline should raise WallClockTimeoutError (not generic TimeoutError)."""
        from pubnub.request_handlers.async_httpx import AsyncHttpxRequestHandler, WallClockTimeoutError

        handler = AsyncHttpxRequestHandler.__new__(AsyncHttpxRequestHandler)
        handler._session = MagicMock()

        async def never_completes(**kwargs):
            await asyncio.sleep(3600)

        handler._session.request = never_completes

        async def run_test():
            real_time = time.time
            start = real_time()
            call_count = [0]

            def mock_time():
                call_count[0] += 1
                if call_count[0] <= 3:
                    return real_time()
                return start + 60

            with patch('pubnub.request_handlers.async_httpx.time') as mock_time_module:
                mock_time_module.time = mock_time
                original = AsyncHttpxRequestHandler.WALL_CLOCK_CHECK_INTERVAL
                AsyncHttpxRequestHandler.WALL_CLOCK_CHECK_INTERVAL = 0.1
                try:
                    with self.assertRaises(WallClockTimeoutError):
                        await handler._request_with_wall_clock_deadline(
                            {"method": "GET", "url": "http://test"},
                            timeout=10
                        )
                finally:
                    AsyncHttpxRequestHandler.WALL_CLOCK_CHECK_INTERVAL = original

        asyncio.run(run_test())

    def test_async_wall_clock_timeout_maps_to_timeout_category(self):
        """WallClockTimeoutError should produce PNTimeoutCategory in request_future."""
        from pubnub.request_handlers.async_httpx import WallClockTimeoutError
        from pubnub.pubnub_asyncio import PubNubAsyncio
        from pubnub.pnconfiguration import PNConfiguration
        from pubnub.enums import PNStatusCategory

        config = PNConfiguration()
        config.subscribe_key = 'demo'
        config.publish_key = 'demo'
        config.user_id = 'test'

        async def run_test():
            pubnub = PubNubAsyncio(config)

            async def mock_async_request(options_func, cancellation_event):
                raise WallClockTimeoutError("Wall-clock deadline exceeded")

            pubnub._request_handler.async_request = mock_async_request

            try:
                # Build an options_func the same way endpoints do
                time_endpoint = pubnub.time()

                def options_func():
                    time_endpoint.validate_params()
                    return time_endpoint.options()

                result = await pubnub.request_future(options_func, None)
                self.assertTrue(result.is_error())
                self.assertEqual(
                    result.status.category,
                    PNStatusCategory.PNTimeoutCategory
                )
            finally:
                await pubnub.stop()

        asyncio.run(run_test())


class TestForceShutdownConnections(unittest.TestCase):
    """Tests for _force_shutdown_connections which uses socket.shutdown(SHUT_RDWR)
    to interrupt blocked reads on macOS."""

    def test_shutdown_calls_socket_shutdown(self):
        """Verify the correct httpcore attribute path is traversed to reach the socket."""
        from pubnub.request_handlers.httpx import WallClockDeadlineWatchdog

        mock_sock = MagicMock()
        mock_stream = MagicMock()
        mock_stream._sock = mock_sock

        mock_inner_conn = MagicMock()
        mock_inner_conn._network_stream = mock_stream

        mock_conn = MagicMock()
        mock_conn._connection = mock_inner_conn

        mock_pool = MagicMock()
        mock_pool._connections = [mock_conn]

        mock_transport = MagicMock()
        mock_transport._pool = mock_pool

        mock_session = MagicMock()
        mock_session._transport = mock_transport

        WallClockDeadlineWatchdog._force_shutdown_connections(mock_session)

        import socket as sock_module
        mock_sock.shutdown.assert_called_once_with(sock_module.SHUT_RDWR)
        mock_session.close.assert_called_once()

    def test_shutdown_degrades_gracefully_on_missing_attrs(self):
        """If httpcore internals change, should not raise — just fall back to session.close()."""
        from pubnub.request_handlers.httpx import WallClockDeadlineWatchdog

        mock_session = MagicMock()
        del mock_session._transport  # Simulate missing attribute

        # Should not raise
        WallClockDeadlineWatchdog._force_shutdown_connections(mock_session)
        mock_session.close.assert_called_once()

    def test_shutdown_with_real_httpx_client(self):
        """Verify the attribute path works with a real httpx.Client after a request."""
        from pubnub.request_handlers.httpx import WallClockDeadlineWatchdog

        client = httpx.Client()
        try:
            client.get('https://ps.pndsn.com/time/0')
        except Exception:
            client.close()
            return  # Skip if network unavailable

        # Verify the path exists
        pool = client._transport._pool
        self.assertTrue(len(pool._connections) > 0)
        conn = pool._connections[0]
        inner = conn._connection
        stream = inner._network_stream
        sock = stream._sock
        self.assertTrue(hasattr(sock, 'shutdown'))

        # Now test the method
        WallClockDeadlineWatchdog._force_shutdown_connections(client)
        self.assertTrue(client.is_closed)


if __name__ == '__main__':
    unittest.main()
