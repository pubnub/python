import unittest
import logging
import time
import pubnub
import threading

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, SubscribeListener

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def test_no_credentials_specified_error(self):
        pnconf = PNConfiguration()
        pubnub = PubNub(pnconf)

        pubnub.add_listener(SubscribeListener())
        pubnub.subscribe().channels('blah').execute()
        time.sleep(3)
        # pubnub.stop()
