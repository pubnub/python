# PubNub HereNow usage example
import logging
import sys

sys.path.append("../")

import pubnub
from examples import pnconf
from pubnub.pubnub import PubNub

pubnub.set_stream_logger('pubnub', logging.DEBUG, stream=sys.stdout)

pnconf.publish_key="blah"
pubnub = PubNub(pnconf)

def success(msg):
    print("success", msg)

def error(err):
    print("error", err)

thread = pubnub.publish() \
    .channel("blah") \
    .message("hey") \
    .async(success, error)

thread.join()
