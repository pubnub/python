import pytest

from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.models.consumer.pubsub import PNFireResult
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/publish/fire_get.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
async def test_single_channel():
    config = pnconf_env_copy()
    config.enable_subscribe = False
    pn = PubNubAsyncio(config)
    chan = 'unique_sync'
    envelope = await pn.fire().channel(chan).message('bla').future()

    assert isinstance(envelope, AsyncioEnvelope)
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNFireResult)
    assert isinstance(envelope.status, PNStatus)
    await pn.stop()
