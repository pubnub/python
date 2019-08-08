import pytest

from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.pnconfiguration import PNConfiguration
from tests.integrational.vcr_helper import pn_vcr


@pytest.fixture
def pnconf():
    pnconf = PNConfiguration()
    pnconf.publish_key = 'demo'
    pnconf.subscribe_key = 'demo'
    pnconf.enable_subscribe = False
    return pnconf


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/signal/single.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_single_channel(pnconf, event_loop):
    pn = PubNubAsyncio(pnconf, custom_event_loop=event_loop)
    chan = 'unique_sync'
    envelope = yield from pn.signal().channel(chan).message('test').future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert envelope.result.timetoken == '15640051159323676'
    assert isinstance(envelope.result, PNSignalResult)
    assert isinstance(envelope.status, PNStatus)
    pn.stop()
