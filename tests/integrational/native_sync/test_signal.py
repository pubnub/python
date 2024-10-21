from urllib.parse import parse_qs, urlparse
from pubnub.pubnub import PubNub
from pubnub.models.consumer.signal import PNSignalResult
from pubnub.models.consumer.common import PNStatus
from pubnub.structures import Envelope
from tests.helper import pnconf_demo_copy, pnconf_env
from tests.integrational.vcr_helper import pn_vcr


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


def test_signal_custom_message_type():
    with pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/signal/signal_custom_message_type.json',
                             filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json') as cassette:
        envelope = PubNub(pnconf_env).signal() \
            .channel("ch1") \
            .message("hi") \
            .custom_message_type('test_message') \
            .sync()

        assert isinstance(envelope.result, PNSignalResult)
        assert int(envelope.result.timetoken) > 1
        assert len(cassette) == 1
        uri = urlparse(cassette.requests[0].uri)
        query = parse_qs(uri.query)
        assert 'custom_message_type' in query.keys()
        assert query['custom_message_type'] == ['test_message']
