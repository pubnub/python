import pytest

from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.models.consumer.pubsub import PNFireResult
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/publish/fire_get.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_single_channel(event_loop):
    config = pnconf_copy()
    config.enable_subscribe = False
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    chan = 'unique_sync'
    envelope = yield from pn.fire().channel(chan).message('bla').future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNFireResult)
    assert isinstance(envelope.status, PNStatus)
    pn.stop()
