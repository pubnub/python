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
        from tests.helper import pnconf_copy

        handler = HttpxRequestHandler(MagicMock())
        # Start the watchdog by setting a deadline
        handler._watchdog.set_deadline(handler.session, time.time() + 300)
        self.assertIsNotNone(handler._watchdog._thread)

        handler.close()
        time.sleep(0.2)

        self.assertTrue(handler._watchdog._stop.is_set())


if __name__ == '__main__':
    unittest.main()
