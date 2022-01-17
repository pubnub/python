import pytest

from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_demo_copy


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/signal/uuid.yaml',
    filter_query_parameters=['seqn', 'pnsdk', 'l_sig']
)
@pytest.mark.asyncio
async def test_single_channel(event_loop):
    pnconf_demo = pnconf_demo_copy()
    pn = PubNubAsyncio(pnconf_demo, custom_event_loop=event_loop)
    chan = 'unique_sync'
    envelope = await pn.signal().channel(chan).message('test').future()

    assert isinstance(envelope, AsyncioEnvelope)
    assert not envelope.status.is_error()
    assert envelope.result.timetoken == '15640051159323676'
    assert isinstance(envelope.result, PNSignalResult)
    assert isinstance(envelope.status, PNStatus)

    pnconf_demo.uuid = 'new-uuid'
    envelope = await pn.signal().channel(chan).message('test').future()
    assert isinstance(envelope, AsyncioEnvelope)
    assert not envelope.status.is_error()
    assert envelope.result.timetoken == '15640051159323677'
    assert isinstance(envelope.result, PNSignalResult)
    assert isinstance(envelope.status, PNStatus)

    await pn.stop()


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


def test_whitespace_uuid_validation_at_setting(event_loop):
    with pytest.raises(AssertionError) as exception:
        pnconf = PNConfiguration()
        pnconf.publish_key = "demo"
        pnconf.subscribe_key = "demo"
        pnconf.uuid = " "

    assert str(exception.value) == 'UUID missing or invalid type'
