import logging

import asyncio
import pytest
import pubnub as pn

from unittest.mock import patch
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope, PubNubAsyncioException
from tests.helper import pnconf_enc_env_copy, pnconf_pam_env_copy, pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "asyncio-int-publish"


@pytest.mark.asyncio
async def assert_success_await(pubnub):
    envelope = await pubnub.future()

    assert isinstance(envelope, AsyncioEnvelope)
    assert isinstance(envelope.result, PNPublishResult)
    assert isinstance(envelope.status, PNStatus)
    assert envelope.result.timetoken > 0
    assert len(envelope.status.original_response) > 0


@pytest.mark.asyncio
async def assert_client_side_error(pubnub, expected_err_msg):
    try:
        await pubnub.future()
    except PubNubException as e:
        assert expected_err_msg in str(e)


@pytest.mark.asyncio
async def assert_success_publish_get(pubnub, msg):
    await assert_success_await(pubnub.publish().channel(ch).message(msg))


@pytest.mark.asyncio
async def assert_success_publish_post(pubnub, msg):
    await assert_success_await(pubnub.publish().channel(ch).message(msg).use_post(True))


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/mixed_via_get.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature']
)
@pytest.mark.asyncio
async def test_publish_mixed_via_get():
    pubnub = PubNubAsyncio(pnconf_env_copy())
    await asyncio.gather(
        asyncio.ensure_future(assert_success_publish_get(pubnub, "hi")),
        asyncio.ensure_future(assert_success_publish_get(pubnub, 5)),
        asyncio.ensure_future(assert_success_publish_get(pubnub, True)),
        asyncio.ensure_future(assert_success_publish_get(pubnub, ["hi", "hi2", "hi3"]))
    )

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/object_via_get.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'],
    match_on=['method', 'scheme', 'host', 'port', 'object_in_path', 'query']
)
@pytest.mark.asyncio
async def test_publish_object_via_get():
    pubnub = PubNubAsyncio(pnconf_env_copy())
    await asyncio.ensure_future(assert_success_publish_get(pubnub, {"name": "Alex", "online": True}))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/mixed_via_post.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'])
@pytest.mark.asyncio
async def test_publish_mixed_via_post():
    pubnub = PubNubAsyncio(pnconf_env_copy())
    await asyncio.gather(
        asyncio.ensure_future(assert_success_publish_post(pubnub, "hi")),
        asyncio.ensure_future(assert_success_publish_post(pubnub, 5)),
        asyncio.ensure_future(assert_success_publish_post(pubnub, True)),
        asyncio.ensure_future(assert_success_publish_post(pubnub, ["hi", "hi2", "hi3"])))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/object_via_post.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'],
    match_on=['method', 'scheme', 'host', 'port', 'path', 'query', 'object_in_body'])
@pytest.mark.asyncio
async def test_publish_object_via_post():
    pubnub = PubNubAsyncio(pnconf_env_copy())
    await asyncio.ensure_future(assert_success_publish_post(pubnub, {"name": "Alex", "online": True}))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/mixed_via_get_encrypted.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'])
@pytest.mark.asyncio
async def test_publish_mixed_via_get_encrypted():
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        pubnub = PubNubAsyncio(pnconf_enc_env_copy())
        await asyncio.gather(
            asyncio.ensure_future(assert_success_publish_get(pubnub, "hi")),
            asyncio.ensure_future(assert_success_publish_get(pubnub, 5)),
            asyncio.ensure_future(assert_success_publish_get(pubnub, True)),
            asyncio.ensure_future(assert_success_publish_get(pubnub, ["hi", "hi2", "hi3"])))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/object_via_get_encrypted.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'],
    match_on=['host', 'method', 'query']
)
@pytest.mark.asyncio
async def test_publish_object_via_get_encrypted():
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        pubnub = PubNubAsyncio(pnconf_enc_env_copy())
        await asyncio.ensure_future(assert_success_publish_get(pubnub, {"name": "Alex", "online": True}))

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/mixed_via_post_encrypted.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'],
    match_on=['method', 'path', 'query', 'body']
)
@pytest.mark.asyncio
async def test_publish_mixed_via_post_encrypted():
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        pubnub = PubNubAsyncio(pnconf_enc_env_copy())
        await asyncio.gather(
            asyncio.ensure_future(assert_success_publish_post(pubnub, "hi")),
            asyncio.ensure_future(assert_success_publish_post(pubnub, 5)),
            asyncio.ensure_future(assert_success_publish_post(pubnub, True)),
            asyncio.ensure_future(assert_success_publish_post(pubnub, ["hi", "hi2", "hi3"]))
        )

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/object_via_post_encrypted.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'],
    match_on=['method', 'path', 'query']
)
@pytest.mark.asyncio
async def test_publish_object_via_post_encrypted():
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        pubnub = PubNubAsyncio(pnconf_enc_env_copy())
        await asyncio.ensure_future(assert_success_publish_post(pubnub, {"name": "Alex", "online": True}))

    await pubnub.stop()


@pytest.mark.asyncio
async def test_error_missing_message():
    pubnub = PubNubAsyncio(pnconf_env_copy())
    await assert_client_side_error(pubnub.publish().channel(ch).message(None), "Message missing")

    await pubnub.stop()


@pytest.mark.asyncio
async def test_error_missing_channel():
    pubnub = PubNubAsyncio(pnconf_env_copy())
    await assert_client_side_error(pubnub.publish().channel("").message("hey"), "Channel missing")

    await pubnub.stop()


@pytest.mark.asyncio
async def test_error_non_serializable():
    pubnub = PubNubAsyncio(pnconf_env_copy())

    def method():
        pass

    await assert_client_side_error(pubnub.publish().channel(ch).message(method), "not JSON serializable")
    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/meta_object.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'],
    match_on=['host', 'method', 'path', 'meta_object_in_query'])
@pytest.mark.asyncio
async def test_publish_with_meta():
    pubnub = PubNubAsyncio(pnconf_env_copy())

    await assert_success_await(pubnub.publish().channel(ch).message("hey").meta({'a': 2, 'b': 'qwer'}))
    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/do_not_store.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'])
@pytest.mark.asyncio
async def test_publish_do_not_store():
    pubnub = PubNubAsyncio(pnconf_env_copy())

    await assert_success_await(pubnub.publish().channel(ch).message("hey").should_store(False))
    await pubnub.stop()


@pytest.mark.asyncio
async def assert_server_side_error_yield(publish_builder, expected_err_msg):
    try:
        await publish_builder.future()
    except PubNubAsyncioException as e:
        assert expected_err_msg in str(e)


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/invalid_key.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub', 'signature'])
@pytest.mark.asyncio
async def test_error_invalid_key():
    pnconf = pnconf_pam_env_copy()

    pubnub = PubNubAsyncio(pnconf)

    await assert_server_side_error_yield(pubnub.publish().channel(ch).message("hey"), "Invalid Key")
    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/not_permitted.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'signature', 'timestamp', 'pnsdk', 'l_pub', 'signature'])
@pytest.mark.asyncio
async def test_not_permitted():
    pnconf = pnconf_pam_env_copy()
    pnconf.secret_key = None
    pubnub = PubNubAsyncio(pnconf)

    await assert_server_side_error_yield(pubnub.publish().channel(ch).message("hey"), "HTTP Client Error (403")
    await pubnub.stop()


@pytest.mark.asyncio
async def test_publish_super_admin_call():
    pubnub = PubNubAsyncio(pnconf_pam_env_copy())

    await pubnub.publish().channel(ch).message("hey").future()
    await pubnub.publish().channel("f#!|oo.bar").message("hey^&#$").should_store(True).meta({
        'name': 'alex'
    }).future()

    await pubnub.stop()
