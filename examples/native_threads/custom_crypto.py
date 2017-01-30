# PubNub custom crypto library usage example
import logging
import os
import sys

d = os.path.dirname
PUBNUB_ROOT = d(d(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PUBNUB_ROOT)

import pubnub

pubnub.set_stream_logger('pubnub', logging.DEBUG, stream=sys.stdout)

from examples import pnconf
from pubnub.pubnub import PubNub
from pubnub.crypto_legacy import PubNubCryptoLegacy

crypto = PubNubCryptoLegacy()

pnconf.enable_subscribe = False
pnconf.cipher_key = 'blah'
pnconf.crypto_instance = crypto
pubnub = PubNub(pnconf)


envelope = pubnub.publish() \
    .channel("blah") \
    .message("hey") \
    .sync()

print(envelope.result)
