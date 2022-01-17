import logging

import asyncio
import pytest
import pubnub as pn

from unittest.mock import patch
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope, PubNubAsyncioException
from tests.helper import pnconf_copy, pnconf_enc_copy, pnconf_pam_copy
from tests.integrational.vcr_helper import pn_vcr

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "asyncio-int-publish"


@pytest.mark.asyncio
async def assert_success_await(pub):
    envelope = await pub.future()

    assert isinstance(envelope, AsyncioEnvelope)
    assert isinstance(envelope.result, PNPublishResult)
    assert isinstance(envelope.status, PNStatus)
    assert envelope.result.timetoken > 0
    assert len(envelope.status.original_response) > 0


@pytest.mark.asyncio
async def assert_client_side_error(pub, expected_err_msg):
    try:
        await pub.future()
    except PubNubException as e:
        assert expected_err_msg in str(e)


@pytest.mark.asyncio
async def assert_success_publish_get(pubnub, msg):
    await assert_success_await(pubnub.publish().channel(ch).message(msg))


@pytest.mark.asyncio
async def assert_success_publish_post(pubnub, msg):
    await assert_success_await(pubnub.publish().channel(ch).message(msg).use_post(True))


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/mixed_via_get.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
async def test_publish_mixed_via_get(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    await asyncio.gather(
        asyncio.ensure_future(assert_success_publish_get(pubnub, "hi")),
        asyncio.ensure_future(assert_success_publish_get(pubnub, 5)),
        asyncio.ensure_future(assert_success_publish_get(pubnub, True)),
        asyncio.ensure_future(assert_success_publish_get(pubnub, ["hi", "hi2", "hi3"]))
    )

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/object_via_get.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
    match_on=['method', 'scheme', 'host', 'port', 'object_in_path', 'query']
)
@pytest.mark.asyncio
async def test_publish_object_via_get(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    await asyncio.ensure_future(assert_success_publish_get(pubnub, {"name": "Alex", "online": True}))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/mixed_via_post.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
async def test_publish_mixed_via_post(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    await asyncio.gather(
        asyncio.ensure_future(assert_success_publish_post(pubnub, "hi")),
        asyncio.ensure_future(assert_success_publish_post(pubnub, 5)),
        asyncio.ensure_future(assert_success_publish_post(pubnub, True)),
        asyncio.ensure_future(assert_success_publish_post(pubnub, ["hi", "hi2", "hi3"])))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/object_via_post.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
    match_on=['method', 'scheme', 'host', 'port', 'path', 'query', 'object_in_body'])
@pytest.mark.asyncio
async def test_publish_object_via_post(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    await asyncio.ensure_future(assert_success_publish_post(pubnub, {"name": "Alex", "online": True}))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/mixed_via_get_encrypted.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
async def test_publish_mixed_via_get_encrypted(event_loop):
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        pubnub = PubNubAsyncio(pnconf_enc_copy(), custom_event_loop=event_loop)
        await asyncio.gather(
            asyncio.ensure_future(assert_success_publish_get(pubnub, "hi")),
            asyncio.ensure_future(assert_success_publish_get(pubnub, 5)),
            asyncio.ensure_future(assert_success_publish_get(pubnub, True)),
            asyncio.ensure_future(assert_success_publish_get(pubnub, ["hi", "hi2", "hi3"])))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/object_via_get_encrypted.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
    match_on=['host', 'method', 'query']
)
@pytest.mark.asyncio
async def test_publish_object_via_get_encrypted(event_loop):
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        pubnub = PubNubAsyncio(pnconf_enc_copy(), custom_event_loop=event_loop)
        await asyncio.ensure_future(assert_success_publish_get(pubnub, {"name": "Alex", "online": True}))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/mixed_via_post_encrypted.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
    match_on=['method', 'path', 'query', 'body']
)
@pytest.mark.asyncio
async def test_publish_mixed_via_post_encrypted(event_loop):
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        pubnub = PubNubAsyncio(pnconf_enc_copy(), custom_event_loop=event_loop)
        await asyncio.gather(
            asyncio.ensure_future(assert_success_publish_post(pubnub, "hi")),
            asyncio.ensure_future(assert_success_publish_post(pubnub, 5)),
            asyncio.ensure_future(assert_success_publish_post(pubnub, True)),
            asyncio.ensure_future(assert_success_publish_post(pubnub, ["hi", "hi2", "hi3"]))
        )

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/object_via_post_encrypted.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
    match_on=['method', 'path', 'query']
)
@pytest.mark.asyncio
async def test_publish_object_via_post_encrypted(event_loop):
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        pubnub = PubNubAsyncio(pnconf_enc_copy(), custom_event_loop=event_loop)
        await asyncio.ensure_future(assert_success_publish_post(pubnub, {"name": "Alex", "online": True}))

    await pubnub.stop()


@pytest.mark.asyncio
async def test_error_missing_message(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    await assert_client_side_error(pubnub.publish().channel(ch).message(None), "Message missing")

    await pubnub.stop()


@pytest.mark.asyncio
async def test_error_missing_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    await assert_client_side_error(pubnub.publish().channel("").message("hey"), "Channel missing")

    await pubnub.stop()


@pytest.mark.asyncio
async def test_error_non_serializable(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)

    def method():
        pass

    await assert_client_side_error(pubnub.publish().channel(ch).message(method), "not JSON serializable")
    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/meta_object.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'],
    match_on=['host', 'method', 'path', 'meta_object_in_query'])
@pytest.mark.asyncio
async def test_publish_with_meta(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)

    await assert_success_await(pubnub.publish().channel(ch).message("hey").meta({'a': 2, 'b': 'qwer'}))
    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/do_not_store.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
async def test_publish_do_not_store(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)

    await assert_success_await(pubnub.publish().channel(ch).message("hey").should_store(False))
    await pubnub.stop()


@pytest.mark.asyncio
async def assert_server_side_error_yield(pub, expected_err_msg):
    try:
        await pub.future()
    except PubNubAsyncioException as e:
        assert expected_err_msg in str(e)


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/invalid_key.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
async def test_error_invalid_key(event_loop):
    pnconf = pnconf_pam_copy()

    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    await assert_server_side_error_yield(pubnub.publish().channel(ch).message("hey"), "Invalid Key")
    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/not_permitted.yaml',
    filter_query_parameters=['uuid', 'seqn', 'signature', 'timestamp', 'pnsdk'])
@pytest.mark.asyncio
async def test_not_permitted(event_loop):
    pnconf = pnconf_pam_copy()
    pnconf.secret_key = None
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    await assert_server_side_error_yield(pubnub.publish().channel(ch).message("hey"), "HTTP Client Error (403")
    await pubnub.stop()


@pytest.mark.asyncio
async def test_publish_super_admin_call(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)

    await pubnub.publish().channel(ch).message("hey").future()
    await pubnub.publish().channel("f#!|oo.bar").message("hey^&#$").should_store(True).meta({
        'name': 'alex'
    }).future()

    await pubnub.stop()
