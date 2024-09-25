import asyncio
import logging
import sys

from pubnub.callbacks import SubscribeCallback
from pubnub.models.consumer.common import PNStatus
from pubnub.pubnub_asyncio import PubNubAsyncio
from pubnub.pnconfiguration import PNConfiguration
from pubnub.enums import PNReconnectionPolicy, PNStatusCategory

config = PNConfiguration()
config.subscribe_key = "demo"
config.publish_key = "demo"
config.enable_subscribe = True
config.uuid = "test-uuid"
config.origin = "127.0.0.1"
config.ssl = False
config.reconnect_policy = PNReconnectionPolicy.NONE

pubnub = PubNubAsyncio(config)

logger = logging.getLogger("pubnub")
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.WARNING)
logger.addHandler(handler)


class SampleCallback(SubscribeCallback):
    message_result = None
    status_result = None
    presence_result = None

    def status(self, pubnub, status):
        self.status_result = status

    def message(self, pubnub, message):
        self.message_result = message

    def presence(self, pubnub, presence):
        self.presence_result = presence


async def main():
    listener = SampleCallback()
    pubnub.add_listener(listener)
    pubnub.subscribe().channels("my_channel").execute()
    while True:
        if isinstance(listener.status_result, PNStatus) \
           and listener.status_result.category == PNStatusCategory.PNDisconnectedCategory:
            print('Could not connect. Exiting...')
            break
        await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
