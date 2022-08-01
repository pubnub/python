import pytest

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from pubnub.structures import Envelope
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_demo_copy


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/signal/uuid.yaml',
                     filter_query_parameters=['seqn', 'pnsdk'])
def test_change_uuid():
    pnconf = pnconf_demo_copy()
    pn = PubNub(pnconf)

    chan = 'unique_sync'
    envelope = pn.signal().channel(chan).message('test').sync()

    pnconf.uuid = 'new-uuid'
    envelope = pn.signal().channel(chan).message('test').sync()

    assert isinstance(envelope, Envelope)
    assert not envelope.status.is_error()
    assert envelope.result.timetoken == '15640049765289377'
    assert isinstance(envelope.result, PNSignalResult)
    assert isinstance(envelope.status, PNStatus)


def test_uuid_validation_at_init():
    with pytest.raises(AssertionError) as exception:
        pnconf = PNConfiguration()
        pnconf.publish_key = "demo"
        pnconf.subscribe_key = "demo"
        PubNub(pnconf)

    assert str(exception.value) == 'UUID missing or invalid type'


def test_uuid_validation_at_setting():
    with pytest.raises(AssertionError) as exception:
        pnconf = PNConfiguration()
        pnconf.publish_key = "demo"
        pnconf.subscribe_key = "demo"
        pnconf.uuid = None

    assert str(exception.value) == 'UUID missing or invalid type'


def test_whitespace_uuid_validation_at_init():
    with pytest.raises(AssertionError) as exception:
        pnconf = PNConfiguration()
        pnconf.publish_key = "demo"
        pnconf.subscribe_key = "demo"
        pnconf.uuid = " "

    assert str(exception.value) == 'UUID missing or invalid type'
