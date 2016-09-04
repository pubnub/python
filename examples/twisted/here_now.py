# PubNub HereNow usage example
import sys

sys.path.append("../../")

from pubnub.pubnub_twisted import PubNubTwisted
from pubnub.pnconfiguration import PNConfiguration


pnconf = PNConfiguration()
pubnub = PubNubTwisted(pnconf)


def success(res):
    print("success")
    print(res.total_occupancy)
    pubnub.stop()


def error(err):
    print("error")
    print(err)
    pubnub.stop()


pubnub.here_now() \
    .channels(["ch1", "ch2", "ch3", "demo"]) \
    .include_state(False) \
    .async(success, error)

pubnub.start()
