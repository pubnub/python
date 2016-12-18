import logging

import pytest
import pubnub as pn

from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_ssl_copy
from tests.integrational.vcr_helper import pn_vcr

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "asyncio-int-publish"


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/secure/ssl.yaml',
                     filter_query_parameters=['uuid', 'pnsdk'])
@pytest.mark.asyncio
def test_publish_string_via_get_encrypted(event_loop):
    pubnub = PubNubAsyncio(pnconf_ssl_copy(), custom_event_loop=event_loop)
    res = yield from pubnub.publish().channel(ch).message("hey").future()
    assert res.result.timetoken > 0

    pubnub.stop()
