import argparse
import asyncio

from os import getenv
from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub_asyncio import EventEngineSubscriptionManager, PubNubAsyncio
from pubnub.pnconfiguration import PNConfiguration

parser = argparse.ArgumentParser(description="Chat with others using PubNub")
parser.add_argument("name", help="Your name")
parser.add_argument("channel", help="The channel you want to join")
args = parser.parse_args()


class ExampleCallback(SubscribeCallback):
    def message(self, pubnub, message):
        print(f"{message.publisher}> {message.message}\n")

    def presence(self, pubnub, presence):
        print(f"{presence.event} {presence.uuid}\n")

    def status(self, pubnub, status):
        # print(status.__dict__)
        pass


async def async_input():
    print()
    await asyncio.sleep(0.1)
    return (await asyncio.get_event_loop().run_in_executor(None, input))


async def main():
    name = args.name if args.name else input("Enter your name: ")
    channel = args.channel if args.channel else input("Enter the channel you want to join: ")

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
