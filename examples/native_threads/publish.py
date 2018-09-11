# PubNub HereNow usage example
import logging
import os
import sys

d = os.path.dirname
PUBNUB_ROOT = d(d(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PUBNUB_ROOT)

import pubnub
from examples import pnconf
from pubnub.pubnub import PubNub, NonSubscribeListener


pubnub.set_stream_logger('pubnub', logging.DEBUG, stream=sys.stdout)

pubnub = PubNub(pnconf)


listener = NonSubscribeListener()

pubnub.publish() \
    .channel("blah") \
    .message("hey") \
    .pn_async(listener.callback)

result = listener.await_result_and_reset(5)
# FIX: returns None
print(result)

pubnub.stop()
