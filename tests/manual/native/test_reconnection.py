# subscribe to pubnub channel, push messages into the queue,
# queue worker send send them to cli
import logging
import os
import sys

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PUBNUB_ROOT)

import pubnub as pn

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNReconnectionPolicy, PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


pn.set_stream_logger('pubnub', logging.DEBUG)
logger = logging.getLogger("myapp")


class MySubscribeCallback(SubscribeCallback):
    def status(self, pubnub, status):
        print("### status changed to: %s" % status.category)
        if status.category == PNStatusCategory.PNReconnectedCategory:
            pubnub.stop()

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        pass


pnconf = PNConfiguration()
pnconf.publish_key = "demo"
pnconf.subscribe_key = "demo"
pnconf.origin = "localhost:8089"
pnconf.subscribe_request_timeout = 10
pnconf.reconnect_policy = PNReconnectionPolicy.LINEAR
pubnub = PubNub(pnconf)

time_until_open_again = 8

my_listener = MySubscribeCallback()
pubnub.add_listener(my_listener)
pubnub.subscribe().channels('my_channel').execute()

# atexit.register(pubnub.stop)
