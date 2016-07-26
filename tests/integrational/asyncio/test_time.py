import pytest
from datetime import date

from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf


@pytest.mark.asyncio
def test_single_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    env = yield from pubnub.time().future()

    assert int(env.result) > 0
    assert isinstance(env.result.date_time(), date)

    pubnub.stop()
