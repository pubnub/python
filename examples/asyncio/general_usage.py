import asyncio
import os
import sys

d = os.path.dirname
PUBNUB_ROOT = d(d(os.path.dirname(os.path.abspath(__file__))))
APP_ROOT = d(os.path.abspath(__file__))
sys.path.append(PUBNUB_ROOT)

from pubnub.exceptions import PubNubException
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio

pnconf = PNConfiguration()
pnconf.publish_key = "demo"
pnconf.subscribe_key = "demo"
pubnub = PubNubAsyncio(pnconf)

async def publish_future():
    e = await pubnub.publish().channel("").message("hello!").future()
    if e.is_error():
        print("Error %s" % str(e))
        print("Error category #%d" % e.status.category)
        return
    else:
        print(str(e.result))

async def publish_result():
    try:
        result = await pubnub.publish().channel("").message("hello!").result()
        print(str(result))
    except PubNubException as e:
        print("Error %s" % str(e))
        if e.status is not None:
            print("Error category #%d" % e.status.category)

loop = asyncio.get_event_loop()
loop.run_until_complete(publish_future())
loop.run_until_complete(publish_result())
loop.close()

