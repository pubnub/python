import tornado
from tornado.testing import AsyncTestCase

from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope
from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


class TestSignal(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        config = pnconf_copy()
        self.pn = PubNubTornado(config, custom_ioloop=self.io_loop)

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/signal/single.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_single_channel(self):
        chan = 'unique_sync'
        envelope = yield self.pn.signal().channel(chan).message('test').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert envelope.result.timetoken == '15614849564528142'
        assert isinstance(envelope.result, PNSignalResult)
        assert isinstance(envelope.status, PNStatus)
        self.pn.stop()
