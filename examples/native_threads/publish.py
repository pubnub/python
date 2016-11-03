# PubNub HereNow usage example
import logging
import sys

sys.path.append("../")

import pubnub
from examples import pnconf
from pubnub.pubnub import PubNub, NonSubscribeListener

pubnub.set_stream_logger('pubnub', logging.DEBUG, stream=sys.stdout)

pubnub = PubNub(pnconf)


listener = NonSubscribeListener()

pubnub.publish() \
    .channel("blah") \
    .message("hey") \
    .async(listener.callback)

result = listener.await_result_and_reset(5)
print(result)

pubnub.stop()
