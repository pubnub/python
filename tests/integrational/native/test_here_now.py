from pubnub.pubnub import PubNub

import unittest
import logging
import pubnub
from tests.helper import pnconf

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubSyncHereNow(unittest.TestCase):
    def test_success(self):
        res = PubNub(pnconf).here_now() \
            .channels(["ch1", "ch2", "ch3", "demo"]) \
            .include_state(False) \
            .sync()

        print(res.total_occupancy)


class TestPubNubAsyncHereNow(unittest.TestCase):
    def test_success(self):
        def callback(res, status):
            print("response", res)
            print("status", status)

        thread = PubNub(pnconf).here_now() \
            .channels(["ch1", "ch2", "ch3", "demo"]) \
            .include_state(False) \
            .async(callback)

        print("awaiting")
        thread.join()
        print("finished")
