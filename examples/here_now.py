# PubNub HereNow usage example
import logging
import sys

sys.path.append("../")

import pubnub
from examples import pnconf
from pubnub.pubnub import PubNub

pubnub.set_stream_logger('pubnub', logging.DEBUG, stream=sys.stdout)

pubnub = PubNub(pnconf)

res = pubnub.here_now() \
    .channels(["ch1", "ch2", "ch3", "demo"]) \
    .include_state(False) \
    .sync()

print(res.total_occupancy)
