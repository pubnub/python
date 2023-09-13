from pubnub.pubnub import PubNub
from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from pubnub.structures import Envelope
from tests.helper import pnconf_demo_copy
from tests.integrational.vcr_helper import pn_vcr
from urllib.parse import urlparse, parse_qs


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/signal/single.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_single_channel():
    chan = 'unique_sync'
    pn = PubNub(pnconf_demo_copy())
    envelope = pn.signal().channel(chan).message('test').sync()

    assert isinstance(envelope, Envelope)
    assert not envelope.status.is_error()
    assert envelope.result.timetoken == '15640049765289377'
    assert isinstance(envelope.result, PNSignalResult)
    assert isinstance(envelope.status, PNStatus)


def test_signal_with_user_message_type():
    with pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/signal/with_user_message_type.json',
                             filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json') as cassette:
        envelope = PubNub(pnconf_demo_copy()).signal().channel("ch1").message_type('test_signal').sync()
        assert isinstance(envelope, Envelope)
        assert not envelope.status.is_error()
        assert int(envelope.result.timetoken) > 0
        assert len(cassette) == 1
        uri = urlparse(cassette.requests[0].uri)
        query = parse_qs(uri.query)
        assert 'type' in query.keys()
        assert query['type'] == ['test_signal']


def test_signal_with_space_id():
    with pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/signal/with_space_id.json',
                             filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json') as cassette:
        envelope = PubNub(pnconf_demo_copy()).signal().channel('ch1').space_id('sp1').sync()

        assert isinstance(envelope, Envelope)
        assert int(envelope.result.timetoken) > 1
        assert len(cassette) == 1
        uri = urlparse(cassette.requests[0].uri)
        query = parse_qs(uri.query)
        assert 'space-id' in query.keys()
        assert query['space-id'] == ['sp1']
