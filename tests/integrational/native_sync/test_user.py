from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.structures import Envelope
from pubnub.pubnub import PubNub
from pubnub.models.consumer.user import PNGetUsersResult
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/users_get.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_get_users():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.get_users().include(['externalId', 'profileUrl', 'email',
                                       'custom', 'created', 'updated', 'eTag']).sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetUsersResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 2
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'custom', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'custom', 'created', 'updated', 'eTag']) == set(data[1])
