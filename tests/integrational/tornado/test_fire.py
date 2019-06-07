import tornado
from tornado.testing import AsyncTestCase

from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope
from pubnub.models.consumer.pubsub import PNFireResult
from pubnub.models.consumer.common import PNStatus
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


class TestMessageCount(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        config = pnconf_copy()
        self.pn = PubNubTornado(config, custom_ioloop=self.io_loop)

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/publish/fire_get.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_single_channel(self):
        chan = 'unique_sync'
        envelope = yield self.pn.fire().channel(chan).message('bla').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNFireResult)
        assert isinstance(envelope.status, PNStatus)
        self.pn.stop()
