import asyncio
import pytest

from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio
from pubnub.models.envelopes import AsyncioEnvelope
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_demo_copy


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/signal/uuid.json',
                     filter_query_parameters=['seqn', 'pnsdk', 'l_sig'], serializer='pn_json')
@pytest.mark.asyncio
async def test_change_uuid():
    with pytest.warns(UserWarning):
        pnconf = pnconf_demo_copy()
        pnconf.disable_config_locking = False
        pn = PubNubAsyncio(pnconf)

        chan = 'unique_sync'
        envelope = await pn.signal().channel(chan).message('test').future()

        pnconf.uuid = 'new-uuid'
        envelope = await pn.signal().channel(chan).message('test').future()

        assert isinstance(envelope, AsyncioEnvelope)
        assert not envelope.status.is_error()
        assert envelope.result.timetoken == '17224117487136760'
        assert isinstance(envelope.result, PNSignalResult)
        assert isinstance(envelope.status, PNStatus)


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/signal/uuid_no_lock.json',
                     filter_query_parameters=['seqn', 'pnsdk', 'l_sig'], serializer='pn_json')
@pytest.mark.asyncio
async def test_change_uuid_no_lock():
    pnconf = pnconf_demo_copy()
    pnconf.disable_config_locking = True
    pn = PubNubAsyncio(pnconf)

    chan = 'unique_sync'
    envelope = await pn.signal().channel(chan).message('test').future()

    pnconf.uuid = 'new-uuid'
    envelope = await pn.signal().channel(chan).message('test').future()

    assert isinstance(envelope, AsyncioEnvelope)
    assert not envelope.status.is_error()
    assert envelope.result.timetoken == '17224117494275030'
    assert isinstance(envelope.result, PNSignalResult)
    assert isinstance(envelope.status, PNStatus)


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.run_until_complete(asyncio.sleep(0))
        loop.close()

def test_uuid_validation_at_init(event_loop):
    with pytest.raises(AssertionError) as exception:
        pnconf = PNConfiguration()
        pnconf.publish_key = "demo"
        pnconf.subscribe_key = "demo"
        PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    assert str(exception.value) == 'UUID missing or invalid type'


def test_uuid_validation_at_setting():
    with pytest.raises(AssertionError) as exception:
        pnconf = PNConfiguration()
        pnconf.publish_key = "demo"
        pnconf.subscribe_key = "demo"
        pnconf.uuid = None

    assert str(exception.value) == 'UUID missing or invalid type'


def test_whitespace_uuid_validation_at_setting():
    with pytest.raises(AssertionError) as exception:
        pnconf = PNConfiguration()
        pnconf.publish_key = "demo"
        pnconf.subscribe_key = "demo"
        pnconf.uuid = " "

    assert str(exception.value) == 'UUID missing or invalid type'
