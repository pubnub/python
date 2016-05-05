from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

import unittest


class TestHereNowSuccess(unittest.TestCase):
    def test_blah(self):


        pnconf = PNConfiguration()
        pubnub = PubNub(pnconf)

        res = pubnub.here_now() \
            .channels(["ch1", "ch2", "ch3", "demo"]) \
            .include_state(False) \
            .sync()

        print(res.total_occupancy)
