# subscribe to pubnub channel, push messages into the queue,
# queue worker send send them to cli
import logging
import os
import sys
import atexit

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PUBNUB_ROOT)

import pubnub as pn

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

pn.set_stream_logger('pubnub', logging.DEBUG)
logger = logging.getLogger("myapp")

pnconfig = PNConfiguration()
pnconfig.publish_key = "demo"
pnconfig.subscribe_key = "demo"

pubnub = PubNub(pnconfig)
logger.info("SDK Version: %s", pubnub.SDK_VERSION)

original_sigint = None


class MyListener(SubscribeCallback):
    def presence(self, pubnub, presence):
        pass

    def status(self, pubnub, status):
        print("Status changed, new status: %s" % status)

    def message(self, pubnub, message):
        print("Message %s" % message)


def subscribe():
    listener = MyListener()
    pubnub.add_listener(listener)
    pubnub.subscribe().channels("demo").execute()
    # TODO: exception doesn't raised, but should inside status() callback


if __name__ == '__main__':
    subscribe()


atexit.register(pubnub.unsubscribe().channels('demo').execute)
atexit.register(pubnub.stop)

# TODO: await

# pubnub.stop()
