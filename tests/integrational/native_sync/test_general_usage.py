import logging
import unittest

import pubnub as pn
from pubnub.enums import PNOperationType
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub import PubNub
from pubnub.structures import Envelope
from tests.helper import pnconf_copy

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "ch"
msg = "hey"


class TestPubNubState(unittest.TestCase):
    def test_success_result(self):
        pubnub = PubNub(pnconf_copy())

        result = pubnub.publish().channel(ch).message(msg).result()

        assert isinstance(result, PNPublishResult)

    def test_sdk_error_result(self):
        pubnub = PubNub(pnconf_copy())

        try:
            pubnub.publish().channel("").message(msg).result()
            raise Exception("Should throw exception")
        except PubNubException as e:
            assert "Channel missing" == str(e)
            assert None == e.status

    def test_server_error_result(self):
        cfg = pnconf_copy()
        cfg.publish_key = "wrong_key"
        pubnub = PubNub(cfg)

        try:
            pubnub.publish().channel(ch).message(msg).result()
            raise Exception("Should throw exception")
        except PubNubException as e:
            assert str(e).startswith("HTTP Client Error (400): ")
            assert 400 == e.status.status_code
            assert PNOperationType.PNPublishOperation == e.status.operation

    def test_success_sync(self):
        pubnub = PubNub(pnconf_copy())

        e = pubnub.publish().channel(ch).message(msg).sync()

        assert isinstance(e, Envelope)
        assert isinstance(e.result, PNPublishResult)
        assert isinstance(e.status, PNStatus)

    def test_sdk_error_sync(self):
        pubnub = PubNub(pnconf_copy())

        e = pubnub.publish().channel("").message(msg).sync()
        assert "Channel missing" == str(e)
        assert None == e.status