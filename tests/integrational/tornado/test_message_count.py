import tornado
from tornado.testing import AsyncTestCase

from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope
from pubnub.models.consumer.message_count import PNMessageCountResult
from pubnub.models.consumer.common import PNStatus
from tests.helper import pnconf_mc_copy
from tests.integrational.vcr_helper import pn_vcr


class TestMessageCount(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        config = pnconf_mc_copy()
        config.enable_subscribe = False
        self.pn = PubNubTornado(config, custom_ioloop=self.io_loop)

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/message_count/single.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_cg', 'l_pub'])
    @tornado.testing.gen_test
    def test_single_channel(self):
        chan = 'unique_tornado'
        envelope = yield self.pn.publish().channel(chan).message('bla').future()
        time = envelope.result.timetoken - 10
        envelope = yield self.pn.message_counts().channel(chan).channel_timetokens([time]).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert envelope.result.channels[chan] == 1
        assert isinstance(envelope.result, PNMessageCountResult)
        assert isinstance(envelope.status, PNStatus)

        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/message_count/multi.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_cg', 'l_pub'])
    @tornado.testing.gen_test
    def test_multiple_channels(self):
        chan_1 = 'unique_asyncio_1'
        chan_2 = 'unique_asyncio_2'
        chans = ','.join([chan_1, chan_2])
        envelope = yield self.pn.publish().channel(chan_1).message('something').future()
        time = envelope.result.timetoken - 10
        envelope = yield self.pn.message_counts().channel(chans).channel_timetokens([time, time]).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert envelope.result.channels[chan_1] == 1
        assert envelope.result.channels[chan_2] == 0
        assert isinstance(envelope.result, PNMessageCountResult)
        assert isinstance(envelope.status, PNStatus)

        self.pn.stop()
