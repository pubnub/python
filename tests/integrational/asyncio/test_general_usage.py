import pytest
from datetime import date

from pubnub.enums import PNOperationType
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from tests.helper import pnconf, pnconf_copy

ch = "blah"
msg = "hey"


@pytest.mark.asyncio
def test_success_result(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    res = yield from pubnub.publish().channel(ch).message(msg).result()

    assert isinstance(res, PNPublishResult)

    pubnub.stop()


@pytest.mark.asyncio
def test_sdk_error_result(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    try:
        yield from pubnub.publish().channel("").message(msg).result()
    except PubNubException as e:
        assert "Channel missing" == str(e)
        assert None == e.status

    pubnub.stop()


# e.status code will populated with PNStatus object only for server-side or network error
@pytest.mark.asyncio
def test_server_error_result(event_loop):
    cfg = pnconf_copy()
    cfg.publish_key = "hey"
    pubnub = PubNubAsyncio(cfg, custom_event_loop=event_loop)

    try:
        yield from pubnub.publish().channel(ch).message(msg).result()
    except PubNubException as e:
        assert str(e).startswith("HTTP Client Error (400): ")
        assert 400 == e.status.status_code
        assert PNOperationType.PNPublishOperation == e.status.operation

    pubnub.stop()

@pytest.mark.asyncio
def test_success_future(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    env = yield from pubnub.publish().channel(ch).message(msg).future()

    assert isinstance(env, AsyncioEnvelope)
    assert isinstance(env.result, PNPublishResult)
    assert isinstance(env.status, PNStatus)

    pubnub.stop()

@pytest.mark.asyncio
def test_sdk_error_future(event_loop):
    cfg = pnconf_copy()
    cfg.publish_key = "hey"
    pubnub = PubNubAsyncio(cfg, custom_event_loop=event_loop)

    try:
        yield from pubnub.publish().channel(ch).message(msg).future()
    except PubNubException as e:
        assert str(e).startswith("HTTP Client Error (400): ")
        assert 400 == e.status.status_code
        assert PNOperationType.PNPublishOperation == e.status.operation

    pubnub.stop()

@pytest.mark.asyncio
def test_server_error_future(event_loop):
    cfg = pnconf_copy()
    cfg.publish_key = "hey"
    pubnub = PubNubAsyncio(cfg, custom_event_loop=event_loop)

    try:
        yield from pubnub.publish().channel(ch).message(msg).future()
    except PubNubException as e:
        assert str(e).startswith("HTTP Client Error (400): ")
        assert 400 == e.status.status_code
        assert PNOperationType.PNPublishOperation == e.status.operation

    pubnub.stop()