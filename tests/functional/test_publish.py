import copy
import unittest

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.endpoints.pubsub.publish import Publish
from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name, url_encode
from pubnub.managers import TelemetryManager


class TestPublish(unittest.TestCase):
    def setUp(self):
        self.sm = MagicMock(
            get_next_sequence=MagicMock(return_value=2)
        )

        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            _publish_sequence_manager=self.sm
        )

        self.pubnub.uuid = "UUID_PublishUnitTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.pub = Publish(self.pubnub)

    def test_pub_message(self):
        message = "hi"
        encoded_message = url_encode(message)

        self.pub.channel("ch1").message(message)

        self.assertEqual(self.pub.build_path(), "/publish/%s/%s/0/ch1/0/%s"
                         % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(self.pub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
        })

    def test_pub_list_message(self):
        self.pubnub.uuid = "UUID_PublishUnitTest"

        message = ["hi", "hi2", "hi3"]
        encoded_message = url_encode(message)

        self.pub.channel("ch1").message(message)

        self.assertEqual(self.pub.build_path(), "/publish/%s/%s/0/ch1/0/%s"
                         % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(self.pub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
        })

    def test_pub_with_meta(self):
        self.pubnub.uuid = "UUID_PublishUnitTest"

        message = ["hi", "hi2", "hi3"]
        encoded_message = url_encode(message)
        meta = ['m1', 'm2']

        self.pub.channel("ch1").message(message).meta(meta)

        self.assertEqual(self.pub.build_path(), "/publish/%s/%s/0/ch1/0/%s"
                         % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(self.pub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'meta': '%5B%22m1%22%2C%20%22m2%22%5D',
        })

    def test_pub_store(self):
        self.pubnub.uuid = "UUID_PublishUnitTest"

        message = ["hi", "hi2", "hi3"]
        encoded_message = url_encode(message)

        self.pub.channel("ch1").message(message).should_store(True)

        self.assertEqual(self.pub.build_path(), "/publish/%s/%s/0/ch1/0/%s"
                         % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(self.pub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'store': '1',
        })

    def test_pub_do_not_store(self):
        self.pubnub.uuid = "UUID_PublishUnitTest"

        message = ["hi", "hi2", "hi3"]
        encoded_message = url_encode(message)

        self.pub.channel("ch1").message(message).should_store(False)

        self.assertEqual(self.pub.build_path(), "/publish/%s/%s/0/ch1/0/%s"
                         % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(self.pub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'store': '0',
        })

    def test_pub_with_auth(self):
        conf = copy.copy(pnconf)
        conf.auth_key = "my_auth"

        pubnub = MagicMock(
            spec=PubNub,
            config=conf,
            sdk_name=sdk_name,
            uuid="UUID_PublishUnitTest",
            _publish_sequence_manager=self.sm
        )
        pubnub._telemetry_manager = TelemetryManager()
        pub = Publish(pubnub)
        message = "hey"
        encoded_message = url_encode(message)
        pub.channel("ch1").message(message)

        self.assertEqual(pub.build_path(), "/publish/%s/%s/0/ch1/0/%s"
                         % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(pub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': pubnub.uuid,
            'auth': conf.auth_key,
        })

    def test_pub_encrypted_list_message(self):
        conf = copy.copy(pnconf)
        conf.cipher_key = "testCipher"

        pubnub = MagicMock(
            spec=PubNub,
            config=conf,
            sdk_name=sdk_name,
            uuid="UUID_PublishUnitTest",
            _publish_sequence_manager=self.sm
        )
        pubnub._telemetry_manager = TelemetryManager()
        pub = Publish(pubnub)

        message = ["hi", "hi2", "hi3"]
        encoded_message = "%22FQyKoIWWm7oN27zKyoU0bpjpgx49JxD04EI%2F0a8rg%2Fo%3D%22"

        pub.channel("ch1").message(message)

        self.assertEqual(pub.build_path(), "/publish/%s/%s/0/ch1/0/%s"
                         % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(pub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': pubnub.uuid,
        })
