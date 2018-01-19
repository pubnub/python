import unittest

from pubnub.exceptions import PubNubException
from tests.helper import pnconf
from pubnub.pubnub import PubNub


class TestPubNubHistoryDelete(unittest.TestCase):  # pylint: disable=W0612
    def test_success(self):
        try:
            env = PubNub(pnconf).delete_messages() \
                .channel("my-ch") \
                .start(123) \
                .end(456) \
                .sync()

            print(env)
            assert not env.status.error
        except PubNubException as e:
            self.fail(e)

    def test_super_call(self):
        try:
            env = PubNub(pnconf).delete_messages() \
                .channel("my-ch- |.* $") \
                .start(123) \
                .end(456) \
                .sync()

            print(env)
            assert not env.status.error
        except PubNubException as e:
            self.fail(e)
