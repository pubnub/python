import logging
import sys

sys.path.append("../")

import pubnub
from examples import pnconf
from pubnub.pubnub import PubNub

# Default log-level is ERROR, to override it use pubnub.set_stream_logger helper:
pubnub.set_stream_logger('pubnub', logging.DEBUG, stream=sys.stdout)

pubnub = PubNub(pnconf)

pubnub.publish() \
    .channel("logging") \
    .message("hello") \
    .sync()
