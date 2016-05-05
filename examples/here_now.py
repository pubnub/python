# PubNub HereNow usage example
import sys

sys.path.append("../")

from pubnub.pnconfiguration import PNConfiguration

pnconf = PNConfiguration()
pubnub = PubNub(pnconf)

res = pubnub.here_now() \
    .channels(["ch1", "ch2", "ch3", "demo"]) \
    .include_state(False) \
    .sync()

print(res.total_occupancy)
