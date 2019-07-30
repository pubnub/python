import pytest

from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.models.consumer.membership import PNGetMembersResult, PNGetSpaceMembershipsResult
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/members/get_members.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_get_members(event_loop):
    config = pnconf_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.get_members().space_id('main').limit(10).count(True).include(['custom', 'user']).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetMembersResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 2
    assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[1])
    assert data[0]['user']['id'] == 'user-1'
    assert data[0]['user']['name'] == 'John Doe'


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/members/get_space_memberships.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_get_space_memberships(event_loop):
    config = pnconf_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.get_space_memberships().user_id('charlie').limit(10).count(True)\
        .include(['custom', 'space']).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetSpaceMembershipsResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 2
    assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[0])
    assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[1])
    assert data[0]['space']['id'] == 'my-channel'
    assert data[0]['space']['name'] == 'My space'
