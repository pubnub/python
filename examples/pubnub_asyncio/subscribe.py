import asyncio

from os import getenv
from pubnub.callbacks import SubscribeCallback
from pubnub.crypto import AesCbcCryptoModule
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio

config = PNConfiguration()
config.publish_key = getenv('PUBLISH_KEY', 'demo')
config.subscribe_key = getenv('SUBSCRIBE_KEY', 'demo')
config.cipher_key = getenv('CIPHER_KEY', 'my_cipher_key')
config.crypto_module = AesCbcCryptoModule(config)
config.uuid = 'example-python'
config.enable_subscribe = True

pubnub = PubNubAsyncio(config)


class PrinterCallback(SubscribeCallback):
    def status(self, pubnub, status):
        print(status.category.name)

    def message(self, pubnub, message):
        print(message.message)


async def main():
    pubnub.add_listener(PrinterCallback())
    pubnub.subscribe().channels("example").execute()

    await asyncio.sleep(500)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
