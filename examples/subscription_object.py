import time

from os import getenv
from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


#  Listeners declaration
def on_message(listener):
    def message_callback(message):
        print(f"\033[94mMessage received on: {listener}: \n{message.message}\033[0m\n")
    return message_callback


def on_message_action(listener):
    def message_callback(message_action):
        print(f"\033[5mMessageAction received on: {listener}: \n{message_action.value}\033[0m\n")
    return message_callback


def on_presence(listener):
    def presence_callback(presence):
        print(f"\033[0;32mPresence received on: {listener}: \t{presence.uuid} {presence.event}s "
              f"{presence.subscription or presence.channel}\033[0m")
    return presence_callback


def on_status(listener):
    def status_callback(status):
        print(f"\033[92mStatus received on: {listener}: \t{status.category.name}\033[0m")
    return status_callback


def on_signal(listener):
    def signal_callback(signal):
        print(f"\033[0;36mSignal received on: {listener}: \n{signal.publisher} says: \t{signal.message}\033[0m")
    return signal_callback


def on_channel_metadata(listener):
    def channel_metadata_callback(channel_meta):
        print(f"\033[0;36mChannel metadata received on: {listener}: \n{channel_meta.__dict__}\033[0m")
    return channel_metadata_callback


class PrintListener(SubscribeCallback):
    def status(self, _, status):
        print(f'\033[92mPrintListener.status:\n{status.category.name}\033[0m')

    def message(self, _, message):
        print(f'\033[94mPrintListener.message:\n{message.message}\033[0m')

    def presence(self, _, presence):
        print(f'PrintListener.presence:\n{presence.uuid} {presence.event}s '
              f'{presence.subscription or presence.channel}\033[0m')

    def signal(self, _, signal):
        print(f'PrintListener.signal:\n{signal.message} from {signal.publisher}\033[0m')

    def channel(self, _, channel):
        print(f'\033[0;37mChannel Meta:\n{channel.__dict__}\033[0m')

    def uuid(self, _, uuid):
        print(f'User Meta:\n{uuid.__dict__}\033[0m')

    def membership(self, _, membership):
        print(f'Membership:\n{membership.__dict__}\033[0m')

    def message_action(self, _, message_action):
        print(f'PrintListener.message_action {message_action}\033[0m')

    def file(self, _, file_message):
        print(f' {file_message.__dict__}\033[0m')


channel = 'test'
group_name = 'test-group'

config = PNConfiguration()
config.subscribe_key = getenv("PN_KEY_SUBSCRIBE")
config.publish_key = getenv("PN_KEY_PUBLISH")
config.user_id = "example"
config.enable_subscribe = True
config.daemon = True

pubnub = PubNub(config)
pubnub.add_listener(PrintListener())

# Subscribing

# Channel test, no presence, first channel object
print('Creating channel object for "test"')
test1 = pubnub.channel(f'{channel}')
print('Creating subscription object for "test"')
t1_subscription = test1.subscription()
t1_subscription.on_message = on_message('listener_1')
t1_subscription.on_message_action = on_message_action('listener_1')
t1_subscription.on_presence = on_presence('listener_1')
t1_subscription.on_status = on_status('listener_1')
t1_subscription.on_signal = on_signal('listener_1')

print('We\'re not yet subscribed to channel "test". So let\'s do it now.')
t1_subscription.subscribe(with_presence=True)
print("Now we're subscribed. We should receive status: connected")

# Testing message delivery
publish_result = pubnub.publish() \
    .channel(f'{channel}') \
    .message('Hello channel "test" from PubNub Python SDK') \
    .meta({'lang': 'en'}) \
    .sync()

time.sleep(2)

print('Removing subscription object for "test"')
t1_subscription.unsubscribe()
time.sleep(2)

print('Exiting')
pubnub.stop()
exit(0)
