import logging
import asyncio

import aiohttp
import pytest
import pubnub as pn
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNReconnectionPolicy

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_sub_copy

pn.set_stream_logger('pubnub', logging.DEBUG)


class MySubscribeCallback(SubscribeCallback):
    def status(self, pubnub, status):
        pass

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        pass


@pytest.mark.asyncio
async def test_blah():
    pnconf = pnconf_sub_copy()
    assert isinstance(pnconf, PNConfiguration)
    pnconf.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
    pubnub = PubNubAsyncio(pnconf)
    time_until_open_again = 8

    async def close_soon():
        await asyncio.sleep(2)
        pubnub._connector.close()
        print(">>> connection is broken")

    async def open_again():
        await asyncio.sleep(time_until_open_again)
        await pubnub.set_connector(aiohttp.TCPConnector(conn_timeout=pubnub.config.connect_timeout, verify_ssl=True))
        print(">>> connection is open again")

    async def countdown():
        await asyncio.sleep(2)
        opened = False
        count = time_until_open_again

        while not opened:
            print(">>> %ds to open again" % count)
            count -= 1
            if count <= 0:
                break
            await asyncio.sleep(1)

    my_listener = MySubscribeCallback()
    pubnub.add_listener(my_listener)
    pubnub.subscribe().channels('my_channel').execute()

    asyncio.ensure_future(close_soon())
    asyncio.ensure_future(open_again())
    asyncio.ensure_future(countdown())

    await asyncio.sleep(1000)
