import os
import time

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, SubscribeListener


# this will replace default SubscribeListener with thing that will print out messages to console
class PrintListener(SubscribeListener):
    def status(self, pubnub, status):
        print(f'Status:\n{status.__dict__}')

    def message(self, pubnub, message):
        print(f'Message:\n{message.__dict__}')

    def presence(self, pubnub, presence):
        print(f'Presence:\n{presence.__dict__}')


# here we create configuration for our pubnub instance
config = PNConfiguration()
config.subscribe_key = os.getenv('PN_KEY_SUBSCRIBE')
config.publish_key = os.getenv('PN_KEY_PUBLISH')
config.user_id = 'example'
config.enable_subscribe = True

listener = PrintListener()

pubnub = PubNub(config)
pubnub.add_listener(listener)
sub = pubnub.subscribe().channels(['example']).execute()
print('Subscribed to channel "example"')

time.sleep(1)

sub = pubnub.subscribe().channels(['example', 'example1']).with_presence().execute()
print('Subscribed to channels "example" and "exmample1"')

time.sleep(1)

pub = pubnub.publish() \
    .channel("example") \
    .message("Hello from PubNub Python SDK") \
    .pn_async(lambda result, status: print(result, status))

time.sleep(3)

pubnub.unsubscribe_all()
time.sleep(1)
print('Bye.')
