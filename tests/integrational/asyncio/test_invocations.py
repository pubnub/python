import logging

import pytest
import pubnub as pn

from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope, PubNubAsyncioException
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "asyncio-int-publish"
corrupted_keys = pnconf_copy()
corrupted_keys.publish_key = "blah"
corrupted_keys.subscribe_key = "blah"


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/invocations/future.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
async def test_publish_future(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    result = await pubnub.publish().message('hey').channel('blah').result()
    assert isinstance(result, PNPublishResult)

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/invocations/future_raises_pubnub_error.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
async def test_publish_future_raises_pubnub_error(event_loop):
    pubnub = PubNubAsyncio(corrupted_keys, custom_event_loop=event_loop)

    with pytest.raises(PubNubException) as exinfo:
        await pubnub.publish().message('hey').channel('blah').result()

    assert 'Invalid Subscribe Key' in str(exinfo.value)
    assert 400 == exinfo.value._status_code

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/invocations/future_raises_ll_error.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
async def test_publish_future_raises_lower_level_error(event_loop):
    pubnub = PubNubAsyncio(corrupted_keys, custom_event_loop=event_loop)

    pubnub._connector.close()

    with pytest.raises(RuntimeError) as exinfo:
        await pubnub.publish().message('hey').channel('blah').result()

    assert 'Session is closed' in str(exinfo.value)

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/invocations/envelope.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
async def test_publish_envelope(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    envelope = await pubnub.publish().message('hey').channel('blah').future()
    assert isinstance(envelope, AsyncioEnvelope)
    assert not envelope.is_error()

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/invocations/envelope_raises.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
async def test_publish_envelope_raises(event_loop):
    pubnub = PubNubAsyncio(corrupted_keys, custom_event_loop=event_loop)
    e = await pubnub.publish().message('hey').channel('blah').future()
    assert isinstance(e, PubNubAsyncioException)
    assert e.is_error()
    assert 400 == e.value()._status_code

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/invocations/envelope_raises_ll_error.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
async def test_publish_envelope_raises_lower_level_error(event_loop):
    pubnub = PubNubAsyncio(corrupted_keys, custom_event_loop=event_loop)

    pubnub._connector.close()

    e = await pubnub.publish().message('hey').channel('blah').future()
    assert isinstance(e, PubNubAsyncioException)
    assert e.is_error()
    assert str(e.value()) == 'Session is closed'

    await pubnub.stop()
