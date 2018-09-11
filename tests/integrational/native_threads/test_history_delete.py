import unittest
import threading

from pubnub.pubnub import PubNub
from tests.helper import pnconf


class TestPubNubSuccessHistoryDelete(unittest.TestCase):  # pylint: disable=W0612
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def assert_success(self):
        self.event.wait()
        if self.status.is_error():
            self.fail(str(self.status.error_data.exception))
        self.event.clear()
        self.response = None
        self.status = None

    def test_success(self):
        PubNub(pnconf).delete_messages() \
            .channel("my-ch") \
            .start(123) \
            .end(456) \
            .pn_async(self.callback)

        self.assert_success()

    def test_super_call(self):
        PubNub(pnconf).delete_messages() \
            .channel("my-ch- |.* $") \
            .start(123) \
            .end(456) \
            .pn_async(self.callback)

        self.assert_success()
