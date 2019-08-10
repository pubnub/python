import pytest

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from pubnub.structures import Envelope
from tests.integrational.vcr_helper import pn_vcr


@pytest.fixture
def pn():
    pnconf = PNConfiguration()
    pnconf.publish_key = 'demo'
    pnconf.subscribe_key = 'demo'
    pnconf.enable_subscribe = False
    return PubNub(pnconf)


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/signal/single.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_single_channel(pn):
    chan = 'unique_sync'
    envelope = pn.signal().channel(chan).message('test').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert envelope.result.timetoken == '15640049765289377'
    assert isinstance(envelope.result, PNSignalResult)
    assert isinstance(envelope.status, PNStatus)
