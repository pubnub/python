# PubNub HereNow usage example
import sys

import time


sys.path.append("../../")

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_twisted import PubNubTwisted

pnconf = PNConfiguration()
pnconf.publish_key = "demo"
pnconf.subscribe_key = "demo"
pnconf.enable_subscribe = True

pubnub = PubNubTwisted(pnconf)


class MyListener(SubscribeCallback):
    def status(self, pubnub, status):
        print("status changed: %s" % status)

    def message(self, pubnub, message):
        print("new message: %s" % message)

    def presence(self, pubnub, presence):
        pass


my_listener = MyListener()


pubnub.add_listener(my_listener)

pubnub.subscribe().channels('my_channel').execute()
time.sleep(60)
