import pytest

from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_copy


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/history/delete_success.json", serializer='pn_json',
    filter_query_parameters=['uuid', 'pnsdk']
)
@pytest.mark.asyncio
async def test_success(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)

    res = await pubnub.delete_messages().channel("my-ch").start(123).end(456).future()

    if res.status.is_error():
        raise AssertionError()

    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/history/delete_with_space_and_wildcard_in_channel_name.json",
    filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json'
)
@pytest.mark.asyncio
async def test_delete_with_space_and_wildcard_in_channel_name(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)

    res = await pubnub.delete_messages().channel("my-ch- |.* $").start(123).end(456).future()

    if res.status.is_error():
        raise AssertionError()

    await pubnub.stop()
