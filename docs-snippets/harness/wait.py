"""eventually(): the only way to wait. No fixed sleeps. Retries on AssertionError until the timeout."""
import asyncio
import time


def eventually(fn, timeout=15, interval=0.5, what='condition'):
    deadline = time.monotonic() + timeout
    last = None
    while True:
        try:
            return fn()
        except AssertionError as e:
            last = e
        if time.monotonic() >= deadline:
            raise AssertionError(f'{what} not met within {timeout}s: {last}')
        time.sleep(interval)


async def aeventually(fn, timeout=15, interval=0.5, what='condition'):
    """fn may be a plain function or a coroutine function."""
    deadline = time.monotonic() + timeout
    last = None
    while True:
        try:
            result = fn()
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except AssertionError as e:
            last = e
        if time.monotonic() >= deadline:
            raise AssertionError(f'{what} not met within {timeout}s: {last}')
        await asyncio.sleep(interval)
