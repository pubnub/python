import logging

import pytest
import pubnub as pn

from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope, PubNubAsyncioException
from tests.helper import pnconf_copy, pnconf_enc_copy, pnconf_ssl_copy

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "asyncio-int-publish"


@pytest.mark.asyncio
def test_publish_string_via_get_encrypted(event_loop):
    pubnub = PubNubAsyncio(pnconf_ssl_copy(), custom_event_loop=event_loop)
    res = yield from pubnub.publish().channel(ch).message("hey").future()
    assert res.result.timetoken > 0
