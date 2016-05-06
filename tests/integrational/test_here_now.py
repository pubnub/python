from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

import unittest


class TestPubNubSyncHereNow(unittest.TestCase):
    def test_success(self):
        pnconf = PNConfiguration()
        pubnub = PubNub(pnconf)

        res = pubnub.here_now() \
            .channels(["ch1", "ch2", "ch3", "demo"]) \
            .include_state(False) \
            .sync()

        print(res.total_occupancy)


class TestPubNubAsyncHereNow(unittest.TestCase):
    def test_success(self):
        pnconf = PNConfiguration()
        pubnub = PubNub(pnconf)

        def success(res):
            print("success")
            print(res.total_occupancy)

        def error(err):
            print("error")
            print(err)

        thread = pubnub.here_now() \
            .channels(["ch1", "ch2", "ch3", "demo"]) \
            .include_state(False) \
            .async(success, error)

        print("awaiting")
        thread.join()
        print("finished")

