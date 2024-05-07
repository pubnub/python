import time

from os import getenv
from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


#  Listeners declaration
def on_message(message):
    print(f"\033[94mMessage received on {message.channel}: \n{message.message}\033[0m\n")


def on_presence(presence):
    print(f"\033[0;32mPresence event received on: {presence.subscription or presence.channel}: ",
          f" \t{presence.uuid} {presence.event}s \033[0m")


class PrintListener(SubscribeCallback):
    def status(self, _, status):
        print(f'\033[92mPrintListener.status:\n{status.category.name}\033[0m')


channel = 'test'

config = PNConfiguration()
config.subscribe_key = getenv("PN_KEY_SUBSCRIBE")
config.publish_key = getenv("PN_KEY_PUBLISH")
config.user_id = "example"
config.enable_subscribe = True
config.daemon = True

pubnub = PubNub(config)
pubnub.add_listener(PrintListener())

# Subscribing
channel_1 = pubnub.channel(channel).subscription()
channel_2 = pubnub.channel(f'{channel}.2').subscription(with_presence=True)

subscription_set = pubnub.subscription_set([channel_1, channel_2])
subscription_set.on_message = on_message
subscription_set.on_presence = on_presence

set_subscription = subscription_set.subscribe()

print("Now we're subscribed. We should receive status: connected on PrintListener")
# Testing message delivery
publish_result = pubnub.publish() \
    .channel(f'{channel}') \
    .message('Hello channel "test" from PubNub Python SDK') \
    .meta({'lang': 'en'}) \
    .sync()

publish_result = pubnub.publish() \
    .channel(f'{channel}.2') \
    .message('PubNub Python SDK の Hello チャンネル「test」') \
    .meta({'lang': 'ja'}) \
    .sync()

time.sleep(3)

print('Removing subscription object for "test"')

time.sleep(2)

print('Exiting')
pubnub.stop()
exit(0)
