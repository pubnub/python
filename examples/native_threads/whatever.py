import asyncio
import os
import sys
import random

from pubnub.endpoints.pubsub import Subscribe
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio

d = os.path.dirname
PUBNUB_ROOT = d(d(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PUBNUB_ROOT)

class Sub:
    def __init__(self, loop, pubnub):
        self.task = None
        self._loop = loop
        self._pubnub = pubnub
        self._id = random.randint(1, 99999)
        self._cancelled = False

    def run(self):
        return self._loop.create_task(self.async_run())

    async def async_run(self):
        try:
            print(f"aaa {self._id}")
            if self._cancelled:
                return
            self.req = Subscribe(self._pubnub).channels(["ch1"]).future()
            res = await self.req
            if res.status.is_error():
                print("error")
            print(f"{res.result} {self._id}")
            return res
        except:
            pass

    def cancel(self):
        print(f"cancelling {self._id}")
        self._cancelled = True
        self.req.cancel()

async def run():
    await asyncio.sleep(2)
    print("after")

async def run_and_cancel(loop, pubnub):
    try:
        sub = Sub(loop, pubnub)
        sub.run()
        print("after")
        sub.cancel()
    except:
        pass
    await asyncio.sleep(1)

async def call_after_time(loop, pubnub):
    await asyncio.sleep(3)
    sub = Sub(loop, pubnub)
    sub.run()
    print("after")
    await asyncio.sleep(1)


def main():
    pnconfig = PNConfiguration()
    pnconfig.publish_key = "demo"
    pnconfig.subscribe_key = "demo"
    pnconfig.uuid = "UUID-PUB"
    loop = asyncio.new_event_loop()
    pubnub = PubNubAsyncio(pnconfig, custom_event_loop=loop)
    sub = Sub(loop, pubnub)
    task3 = sub.run()
    task1 = loop.create_task(run())
    task2 = loop.create_task(run_and_cancel(loop, pubnub))
    task4 = loop.create_task(call_after_time(loop, pubnub))
    loop.run_until_complete(asyncio.gather(task1, task2, task4))

main()