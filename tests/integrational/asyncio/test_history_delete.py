import pytest

from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf


@pytest.mark.asyncio
def test_success(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    res = yield from pubnub.delete_messages().channel("my-ch").start(123).end(456).future()

    if res.status.is_error():
        raise AssertionError()


@pytest.mark.asyncio
def test_super_call(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    res = yield from pubnub.delete_messages().channel("my-ch- |.* $").start(123).end(456).future()

    if res.status.is_error():
        raise AssertionError()
