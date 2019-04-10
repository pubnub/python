from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.structures import Envelope
from pubnub.pubnub import PubNub
from pubnub.models.consumer.pubsub import PNFireResult
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/publish/fire_get.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_single_channel():
    config = pnconf_copy()
    pn = PubNub(config)
    chan = 'unique_sync'
    envelope = pn.fire().channel(chan).message('bla').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNFireResult)
    assert isinstance(envelope.status, PNStatus)
