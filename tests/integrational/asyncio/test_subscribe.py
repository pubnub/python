import logging
import asyncio
import pytest
import pubnub as pn
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_copy
from tests.integrational.native.native_helper import SubscribeListener

pn.set_stream_logger('pubnub', logging.DEBUG)


@pytest.mark.asyncio
async def test_subscribe_async_await(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    callback = SubscribeListener()
    pubnub.add_listener(callback)
    pubnub.subscribe() \
        .channels(["ch1", "ch2"]) \
        .execute()

    await callback.wait_for_connect()
    # assert callback.done
    # assert callback.msg.actual_channel == 'ch1'
    # assert callback.msg.subscribed_channel == 'ch1'
    # assert callback.msg.message == 'hey'
    # assert callback.msg.timetoken > 0

    # pubnub.stop()
