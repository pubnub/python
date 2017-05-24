import tornado

from tornado.testing import AsyncTestCase

from pubnub.enums import PNOperationType
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope, PubNubTornadoException
from tests.helper import pnconf, pnconf_copy

ch = "ch"
msg = "hey"


class TestGeneralUsage(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)


    @tornado.testing.gen_test
    def test_success_result(self):
        pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

        envelope = yield pubnub.publish().channel(ch).message(msg).result()

        assert isinstance(envelope, PNPublishResult)


    @tornado.testing.gen_test
    def test_sdk_error_result(self):
        pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

        try:
            yield pubnub.publish().channel("").message(msg).result()
        except PubNubTornadoException as e:
            assert "Channel missing" == str(e)
            assert None == e.status

    @tornado.testing.gen_test
    def test_server_error_result(self):
        cfg = pnconf_copy()
        cfg.publish_key = "hey"

        pubnub = PubNubTornado(cfg, custom_ioloop=self.io_loop)

        try:
            yield pubnub.publish().channel(ch).message(msg).result()
        except PubNubTornadoException as e:
            assert str(e).startswith("HTTP Client Error (400): ")
            assert 400 == e.status.status_code
            assert PNOperationType.PNPublishOperation == e.status.operation

    @tornado.testing.gen_test
    def test_success_future(self):
        pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

        envelope = yield pubnub.publish().channel(ch).message(msg).future()

        assert isinstance(envelope, TornadoEnvelope)
        assert isinstance(envelope.result, PNPublishResult)
        assert isinstance(envelope.status, PNStatus)

    @tornado.testing.gen_test
    def test_sdk_error_future(self):
        pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

        try:
            yield pubnub.publish().channel("").message(msg).future()
        except PubNubTornadoException as e:
            assert "Channel missing" == str(e)
            assert None == e.status

    @tornado.testing.gen_test
    def test_server_error_future(self):
        cfg = pnconf_copy()
        cfg.publish_key = "hey"

        pubnub = PubNubTornado(cfg, custom_ioloop=self.io_loop)

        try:
            yield pubnub.publish().channel(ch).message(msg).future()
        except PubNubTornadoException as e:
            assert str(e).startswith("HTTP Client Error (400): ")
            assert 400 == e.status.status_code
            assert PNOperationType.PNPublishOperation == e.status.operation