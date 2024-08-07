import os
import asyncio

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio, SubscribeCallback
from pubnub.enums import PNStatusCategory


class MySubscribeCallback(SubscribeCallback):
    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            print("Disconnected")
        elif status.category == PNStatusCategory.PNConnectedCategory:
            print("Connected")
        elif status.category == PNStatusCategory.PNReconnectedCategory:
            print("Reconnected")
        elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
            print("Decryption error")

    def message(self, pubnub, message):
        print(f"Received message: {message.message} on channel: {message.channel}")

    def presence(self, pubnub, presence):
        print(f"Presence event: {presence.event}")


async def main(pubnub):
    pubnub.subscribe().channels('my_channel').execute()
    print("Listening for messages...")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY') or 'demo'
    pnconfig.publish_key = os.getenv('PUBNUB_PUBLISH_KEY') or 'demo'
    pnconfig.user_id = "my_unique_user_id"  # Set a unique user ID

    pubnub = PubNubAsyncio(pnconfig)
    callback = MySubscribeCallback()
    pubnub.add_listener(callback)

    try:
        loop.run_until_complete(main(pubnub))
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting...")
    finally:
        loop.run_until_complete(pubnub.stop())  # Assuming 'pubnub' is in scope
        loop.close()
