import os

import sys
from tornado import gen
from tornado.ioloop import IOLoop

d = os.path.dirname
PUBNUB_ROOT = d(d(os.path.dirname(os.path.abspath(__file__))))
APP_ROOT = d(os.path.abspath(__file__))
sys.path.append(PUBNUB_ROOT)

from pubnub.exceptions import PubNubException
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado

pnconf = PNConfiguration()
pnconf.publish_key = "demo"
pnconf.subscribe_key = "demo"
pubnub = PubNubTornado(pnconf)

@gen.coroutine
def publish_future():
    e = yield pubnub.publish().channel("my_channel").message("hello!").future()
    if e.is_error():
        print("Error %s" % str(e))
        print("Error category #%d" % e.status.category)
        return
    else:
        print(str(e.result))

@gen.coroutine
def publish_result():
    try:
        result = yield pubnub.publish().channel("my_channel").message("hello!").result()
        print(str(result))
    except PubNubException as e:
        print("Error %s" % str(e))
        if e.status is not None:
            print("Error category #%d" % e.status.category)

if __name__ == "__main__":
    IOLoop.current().run_sync(publish_future)
    IOLoop.current().run_sync(publish_result)
