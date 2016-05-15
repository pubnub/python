import unittest

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.endpoints.pubsub.publish import Publish
from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name, encode


class TestPublish(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name
        )
        self.pubnub.uuid = "UUID_PublishUnitTest"
        self.pub = Publish(self.pubnub)

    def test_pub_message(self):
        message = "hi"
        encoded_message = encode(message)

        self.pub.channel("ch1").message(message)

        self.assertEquals(self.pub.build_path(), "/publish/%s/%s/0/ch1/0/%s"
                          % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(self.pub.build_params(), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

    def test_pub_list_message(self):
        self.pubnub.uuid = "UUID_PublishUnitTest"

        message = ["hi", "hi2", "hi3"]
        encoded_message = encode(message)

        self.pub.channel("ch1").message(message)

        self.assertEquals(self.pub.build_path(), "/publish/%s/%s/0/ch1/0/%s"
                          % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(self.pub.build_params(), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })


# TODO: auth key
