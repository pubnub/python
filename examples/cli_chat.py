import argparse
import asyncio

from os import getenv
from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub_asyncio import EventEngineSubscriptionManager, PubNubAsyncio
from pubnub.pnconfiguration import PNConfiguration

parser = argparse.ArgumentParser(description="Chat with others using PubNub")
parser.add_argument("-n", metavar="name", help="Your name", default=None, required=False)
parser.add_argument("-c", metavar="channel", help="The channel you want to join", default=None, required=False)
args = parser.parse_args()


class ExampleCallback(SubscribeCallback):
    def message(self, pubnub, message):
        print(f"{message.publisher}> {message.message}\n")

    def presence(self, pubnub, presence):
        print(f"-- {presence.uuid} {'joined' if presence.event == 'join' else 'left'} \n")

    def status(self, pubnub, status):
        if status.is_error():
            print(f"! Error: {status.error_data}")
        else:
            print(f"* Status: {status.category.name}")


async def async_input():
    print()
    await asyncio.sleep(0.1)
    return (await asyncio.get_event_loop().run_in_executor(None, input))


async def main():
    name = args.name if hasattr(args, "name") else input("Enter your name: ")
    channel = args.channel if hasattr(args, "channel") else input("Enter the channel you want to join: ")

    print("Welcome to the chat room. Type 'exit' to leave the chat.")

    config = PNConfiguration()
    config.subscribe_key = getenv("PN_KEY_SUBSCRIBE")
    config.publish_key = getenv("PN_KEY_PUBLISH")
    config.uuid = name

    pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager)
    pubnub.add_listener(ExampleCallback())

    pubnub.subscribe().channels(channel).with_presence().execute()

    while True:
        message = await async_input()
        print("\x1b[2K")
        if message == "exit":
            print("Goodbye!")
            break

        await pubnub.publish().channel(channel).message(message).future()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
