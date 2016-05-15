from pubnub.pubnub import PubNub

import unittest
import logging
import pubnub
from tests.helper import pnconf

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubSyncHereNow(unittest.TestCase):
    def test_success(self):
        pubnub = PubNub(pnconf)

        res = pubnub.here_now() \
            .channels(["ch1", "ch2", "ch3", "demo"]) \
            .include_state(False) \
            .sync()

        print(res.total_occupancy)


class TestPubNubAsyncHereNow(unittest.TestCase):
    def test_success(self):
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
