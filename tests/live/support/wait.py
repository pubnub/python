"""Waits. eventually() retries until one pass succeeds, settled() until several consecutive passes succeed (a read
after a write can hit a lagging replica). sleep() is only for proving that something does NOT happen.

Every wait has a sync and an asyncio twin that share one policy object.
"""
import asyncio
import time
from dataclasses import dataclass

PRESENCE_TIMEOUT = 45
PRESENCE_EVENT_TIMEOUT = 30


@dataclass(frozen=True)
class Policy:
    timeout: float = 15
    interval: float = 0.5
    passes: int = 1


EVENTUALLY = Policy()
SETTLED = Policy(timeout=15, interval=0.75, passes=3)


def _policy(base, timeout, interval, passes):
    return Policy(timeout=base.timeout if timeout is None else timeout,
                  interval=base.interval if interval is None else interval,
                  passes=base.passes if passes is None else passes)


def _poll(fn, policy, what):
    deadline = time.monotonic() + policy.timeout
    last, good, result = None, 0, None
    while True:
        try:
            result = fn()
            good += 1
            if good >= policy.passes:
                return result
        except AssertionError as e:
            last, good = e, 0
        if time.monotonic() >= deadline:
            raise AssertionError(f'{what} not met within {policy.timeout}s '
                                 f'({policy.passes} consecutive passes): {last}')
        time.sleep(policy.interval)


async def _apoll(fn, policy, what):
    deadline = time.monotonic() + policy.timeout
    last, good, result = None, 0, None
    while True:
        try:
            result = fn()
            if asyncio.iscoroutine(result):
                result = await result
            good += 1
            if good >= policy.passes:
                return result
        except AssertionError as e:
            last, good = e, 0
        if time.monotonic() >= deadline:
            raise AssertionError(f'{what} not met within {policy.timeout}s '
                                 f'({policy.passes} consecutive passes): {last}')
        await asyncio.sleep(policy.interval)


def eventually(fn, timeout=None, interval=None, what='condition'):
    """Retries fn on AssertionError until it passes once."""
    return _poll(fn, _policy(EVENTUALLY, timeout, interval, None), what)


async def aeventually(fn, timeout=None, interval=None, what='condition'):
    """fn may be a plain function or a coroutine function."""
    return await _apoll(fn, _policy(EVENTUALLY, timeout, interval, None), what)


def settled(fn, timeout=None, interval=None, passes=None, what='condition'):
    """Retries fn until it passes `passes` times in a row (default 3, 750 ms apart, 15 s)."""
    return _poll(fn, _policy(SETTLED, timeout, interval, passes), what)


async def asettled(fn, timeout=None, interval=None, passes=None, what='condition'):
    return await _apoll(fn, _policy(SETTLED, timeout, interval, passes), what)


def sleep(seconds):
    """Only to prove absence (a fired message is not delivered). Never to wait for a result."""
    time.sleep(seconds)


async def asleep(seconds):
    await asyncio.sleep(seconds)
