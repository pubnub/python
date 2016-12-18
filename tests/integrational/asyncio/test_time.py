import pytest
from datetime import date

from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf
from tests.integrational.vcr_helper import pn_vcr


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/time/get.yaml',
    filter_query_parameters=['uuid', 'pnsdk'])
@pytest.mark.asyncio
def test_time(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    res = yield from pubnub.time().result()

    assert int(res) > 0
    assert isinstance(res.date_time(), date)

    pubnub.stop()
