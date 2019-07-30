from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.structures import Envelope
from pubnub.pubnub import PubNub
from pubnub.models.consumer.membership import PNGetMembersResult, PNGetSpaceMembershipsResult
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/members/get_members.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_get_members():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.get_members().space_id('main').limit(10).count(True).include(['custom', 'user']).sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetMembersResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 2
    assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[1])
    assert data[0]['user']['id'] == 'user-1'
    assert data[0]['user']['name'] == 'John Doe'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/members/get_space_memberships.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_get_space_memberships():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.get_space_memberships().user_id('charlie').limit(10).count(True).include(['custom', 'space']).sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetSpaceMembershipsResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 2
    assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[0])
    assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[1])
    assert data[0]['space']['id'] == 'my-channel'
    assert data[0]['space']['name'] == 'My space'
