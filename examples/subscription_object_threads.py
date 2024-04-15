import time

from os import getenv
from pubnub.callbacks import SubscribeCallback
from pubnub.models.consumer.message_actions import PNMessageAction
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
t1_subscription.subscribe()
print("Now we're subscribed. We should receive status: connected")

time.sleep(3)
print("We don't see any presence event since we don't have it enabled yet")

# Channel test, with presence, second channel object
print('Creating second channel object for "test" and "test.2"')
test2 = pubnub.channel([f'{channel}', f'{channel}.2'])
print('Creating second subscription object for channels "test" and "test.2"')
t2_subscription = test2.subscription(with_presence=True)
t2_subscription.on_message = on_message('listener_2')
t2_subscription.on_presence = on_presence('listener_2')
t2_subscription.on_status = on_status('listener_2')
t2_subscription.on_signal = on_signal('listener_2')
t2_subscription.subscribe()

print('Now we\'re subscribed to "test" with two listeners. one with presence and one without')
print('So we should see presence events only for listener "test2" for channels "test" and "test2"')
time.sleep(2)

# Channel test3, no presence, third channel object
print('Creating channel object for "test.3"')
test3 = pubnub.channel(f'{channel}.3')
print('Creating subscription object for "test.3"')
t3_subscription = test3.subscription()
t3_subscription.on_message = on_message('listener_3')
t3_subscription.on_presence = on_presence('listener_3')
t3_subscription.on_status = on_status('listener_3')
t3_subscription.on_signal = on_signal('listener_3')
print('We subscribe to third channel so we should see three "connected" statuses and no new presence events')
t3_subscription.subscribe()

print('Creating wildcard object for "test.*"')
wildcard_channel = pubnub.channel(f'{channel}.*')
print('Creating wildcard subscription object for "test.*"')
wildcard = wildcard_channel.subscription()
wildcard.on_message = on_message('WILDCARD')
wildcard.on_presence = on_presence('WILDCARD')
wildcard.on_status = on_status('WILDCARD')
wildcard.on_signal = on_signal('WILDCARD')
print('We subscribe to all channels "test.*"')
wildcard.subscribe()

print('Creating Group with "test.2" and "test.3"')
pubnub.add_channel_to_channel_group() \
    .channels(['test']) \
    .channel_group(group_name) \
    .sync()

print('Creating group object for "test_group"')
group = pubnub.channel_group(f'{group_name}')
print('Creating wildcard subscription object for "group_name"')
group_subscription = group.subscription()
group_subscription.on_message = on_message('group')
group_subscription.on_presence = on_presence('group')
group_subscription.on_status = on_status('group')
group_subscription.on_signal = on_signal('group')
print('We subscribe to the channel group "test_group"')
group_subscription.subscribe()

print('Now we publish messages to each channel separately')
time.sleep(1)

# Testing message delivery
publish_result = pubnub.publish() \
    .channel(f'{channel}') \
    .message('Hello channel "test" from PubNub Python SDK') \
    .meta({'lang': 'en'}) \
    .sync()

pubnub.publish() \
    .channel(f'{channel}.2') \
    .message('Nau mai ki te hongere "test.2" mai i PubNub Python SDK') \
    .meta({'lang': 'mi'}) \
    .sync()

pubnub.publish() \
    .channel(f'{channel}.3') \
    .message('Bienvenido al canal "test.3" de PubNub Python SDK') \
    .meta({'lang': 'es'}) \
    .sync()

pubnub.publish() \
    .channel(f'{channel}.4') \
    .message('Ciao canale "test.4" da PubNub Python SDK') \
    .meta({'lang': 'it'}) \
    .sync()

time.sleep(1)

print('Add a signal')
pubnub.signal().channel(channel).message('Ping!').sync()

time.sleep(1)

print('Now let\'s add a reaction to message')
pubnub.add_message_action().channel(channel).message_action(PNMessageAction({
    'type': 'response',
    'value': 'Hi!',
    'messageTimetoken': publish_result.result.timetoken,
    'uuid': config.user_id,
    'actionTimetoken': publish_result.result.timetoken + 1000,
})).sync()

time.sleep(1)

#  USER CONTEXT

print(f'Creating subscription to user "{config.uuid}"')
user_subscription = pubnub.user_metadata(config.uuid).subscription()

print(f'And adding user some context to "{config.uuid}"')
pubnub.set_uuid_metadata().uuid(config.user_id).set_name('Patrick').set_status('ACTIVE') \
    .custom({'IsThisDoggo?': False, 'IsThisPatrick': True}).sync()

time.sleep(3)

print('Removing second subscription object for "test"')
t1_subscription.unsubscribe()
time.sleep(2)

#  Unsubscribing


# pubnub.unsubscribe_all()
# print('We now should be unsubscribed from all channels')

print('Exiting')
pubnub.stop()
exit(0)
