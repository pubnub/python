import pytest

from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/signal/single.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_single_channel(event_loop):
    config = pnconf_copy()
    config.enable_subscribe = False
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    chan = 'unique_sync'
    envelope = yield from pn.signal().channel(chan).message('test').future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert envelope.result.timetoken == '15614849564528142'
    assert isinstance(envelope.result, PNSignalResult)
    assert isinstance(envelope.status, PNStatus)
    pn.stop()
