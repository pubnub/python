import logging
import pytest
import pubnub as pn
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_sub_copy
from tests.integrational.native.native_helper import SubscribeListener

pn.set_stream_logger('pubnub', logging.DEBUG)


@pytest.mark.asyncio
async def test_subscribe_async_await(event_loop):
    conf = pnconf_sub_copy()
    conf.set_presence_timeout(14)
    pubnub = PubNubAsyncio(conf, custom_event_loop=event_loop)

    callback = SubscribeListener()
    pubnub.add_listener(callback)
    pubnub.subscribe().channels("ch1").execute()

    await callback.wait_for_connect()

    pubnub.unsubscribe().channels("ch1").execute()
    await callback.wait_for_disconnect()

    pubnub.stop()
