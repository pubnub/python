import logging

import asyncio
import pytest
import pubnub as pn

from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope, PubNubAsyncioException
from tests.helper import pnconf_copy, pnconf_enc_copy

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "asyncio-int-publish"


@pytest.mark.asyncio
def assert_success_await(pub):
    envelope = yield from pub.future()

    assert isinstance(envelope, AsyncioEnvelope)
    assert isinstance(envelope.result, PNPublishResult)
    assert isinstance(envelope.status, PNStatus)
    assert envelope.result.timetoken > 0
    assert len(envelope.status.original_response) > 0


@pytest.mark.asyncio
def assert_client_side_error(pub, expected_err_msg):
    try:
        yield from pub.future()
    except PubNubException as e:
        assert expected_err_msg in str(e)


@pytest.mark.asyncio
def assert_success_publish_get(pubnub, msg):
    yield from assert_success_await(pubnub.publish().channel(ch).message(msg))


@pytest.mark.asyncio
def assert_success_publish_post(pubnub, msg):
    yield from assert_success_await(pubnub.publish().channel(ch).message(msg).use_post(True))


@pytest.mark.asyncio
def test_publish_string_via_get(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    yield from asyncio.gather(
        asyncio.ensure_future(assert_success_publish_get(pubnub, "hi")),
        asyncio.ensure_future(assert_success_publish_get(pubnub, 5)),
        asyncio.ensure_future(assert_success_publish_get(pubnub, True)),
        asyncio.ensure_future(assert_success_publish_get(pubnub, ["hi", "hi2", "hi3"])),
        asyncio.ensure_future(assert_success_publish_get(pubnub, {"name": "Alex", "online": True})))

    pubnub.stop()


@pytest.mark.asyncio
def test_publish_string_via_post(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    yield from asyncio.gather(
        asyncio.ensure_future(assert_success_publish_post(pubnub, "hi")),
        asyncio.ensure_future(assert_success_publish_post(pubnub, 5)),
        asyncio.ensure_future(assert_success_publish_post(pubnub, True)),
        asyncio.ensure_future(assert_success_publish_post(pubnub, ["hi", "hi2", "hi3"])),
        asyncio.ensure_future(assert_success_publish_post(pubnub, {"name": "Alex", "online": True})))

    pubnub.stop()


@pytest.mark.asyncio
def test_publish_string_via_get_encrypted(event_loop):
    pubnub = PubNubAsyncio(pnconf_enc_copy(), custom_event_loop=event_loop)
    yield from asyncio.gather(
        asyncio.ensure_future(assert_success_publish_get(pubnub, "hi")),
        asyncio.ensure_future(assert_success_publish_get(pubnub, 5)),
        asyncio.ensure_future(assert_success_publish_get(pubnub, True)),
        asyncio.ensure_future(assert_success_publish_get(pubnub, ["hi", "hi2", "hi3"])),
        asyncio.ensure_future(assert_success_publish_get(pubnub, {"name": "Alex", "online": True})))

    pubnub.stop()


@pytest.mark.asyncio
def test_publish_string_via_post_encrypted(event_loop):
    pubnub = PubNubAsyncio(pnconf_enc_copy(), custom_event_loop=event_loop)
    yield from asyncio.gather(
        asyncio.ensure_future(assert_success_publish_post(pubnub, "hi")),
        asyncio.ensure_future(assert_success_publish_post(pubnub, 5)),
        asyncio.ensure_future(assert_success_publish_post(pubnub, True)),
        asyncio.ensure_future(assert_success_publish_post(pubnub, ["hi", "hi2", "hi3"])),
        asyncio.ensure_future(assert_success_publish_post(pubnub, {"name": "Alex", "online": True})))

    pubnub.stop()


@pytest.mark.asyncio
def test_error_missing_message(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    yield from assert_client_side_error(pubnub.publish().channel(ch).message(None), "Message missing")

    pubnub.stop()


@pytest.mark.asyncio
def test_error_missing_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    yield from assert_client_side_error(pubnub.publish().channel("").message("hey"), "Channel missing")

    pubnub.stop()


@pytest.mark.asyncio
def test_error_non_serializable(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)

    def method():
        pass

    yield from assert_client_side_error(pubnub.publish().channel(ch).message(method), "not JSON serializable")
    pubnub.stop()


@pytest.mark.asyncio
def test_publish_with_meta(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)

    yield from assert_success_await(pubnub.publish().channel(ch).message("hey").meta({'a': 2, 'b': 'qwer'}))
    pubnub.stop()


@pytest.mark.asyncio
def test_publish_do_not_store(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)

    yield from assert_success_await(pubnub.publish().channel(ch).message("hey").should_store(False))
    pubnub.stop()


@pytest.mark.asyncio
def assert_server_side_error_yield(pub, expected_err_msg):
    try:
        yield from pub.future()
    except PubNubAsyncioException as e:
        assert expected_err_msg in str(e)


@pytest.mark.asyncio
def test_error_invalid_key(event_loop):
    conf = PNConfiguration()
    conf.publish_key = "fake"
    conf.subscribe_key = "demo"
    conf.enable_subscribe = False

    pubnub = PubNubAsyncio(conf, custom_event_loop=event_loop)

    yield from assert_server_side_error_yield(pubnub.publish().channel(ch).message("hey"), "Invalid Key")
    pubnub.stop()

