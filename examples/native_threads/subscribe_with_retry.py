import logging
import sys
import time

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, SubscribeListener
from pubnub.enums import PNReconnectionPolicy, PNStatusCategory


class TestListener(SubscribeListener):
    status_result = None
    disconnected = False

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNDisconnectedCategory:
            print('Could not connect. Exiting...')
            self.disconnected = True

    def message(self, pubnub, message):
        print(f'Message:\n{message.__dict__}')

    def presence(self, pubnub, presence):
        print(f'Presence:\n{presence.__dict__}')


logger = logging.getLogger("pubnub")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


config = PNConfiguration()
config.subscribe_key = "demo"
config.publish_key = "demo"
config.user_id = 'example'
config.enable_subscribe = True
config.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
config.origin = '127.0.0.1'
config.ssl = False

listener = TestListener()

pubnub = PubNub(config)
pubnub.add_listener(listener)
sub = pubnub.subscribe().channels(['example']).execute()

while not listener.disconnected:
    time.sleep(0.5)
print('Disconnected. Bye.')
