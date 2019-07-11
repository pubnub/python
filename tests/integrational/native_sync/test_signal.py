import pytest

from pubnub.pubnub import PubNub
from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from pubnub.structures import Envelope
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


@pytest.fixture
def pn():
    config = pnconf_copy()
    config.enable_subscribe = False
    return PubNub(config)


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/signal/single.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_single_channel(pn):
    chan = 'unique_sync'
    envelope = pn.signal().channel(chan).message('test').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert envelope.result.timetoken == '15614849564528142'
    assert isinstance(envelope.result, PNSignalResult)
    assert isinstance(envelope.status, PNStatus)
