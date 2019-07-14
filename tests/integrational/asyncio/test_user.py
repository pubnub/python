import pytest

from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.models.consumer.user import PNGetUsersResult, PNCreateUserResult
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/user/users_get.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_get_users(event_loop):
    config = pnconf_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.get_users().include(['externalId', 'profileUrl', 'email',
                                                  'custom', 'created', 'updated', 'eTag']).future()
    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetUsersResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 2
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'custom', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'custom', 'created', 'updated', 'eTag']) == set(data[1])


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/user/create_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_create_user(event_loop):
    config = pnconf_copy()
    pn = PubNubAsyncio(config)
    data = {'id': 'user-1', 'name': 'John Doe',
            'externalId': None, 'profileUrl': None, 'email': 'jack@twitter.com'}
    envelope = yield from pn.create_user().include(data).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNCreateUserResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert data['id'] == 'user-1'
    assert data['name'] == 'John Doe'
    assert data['externalId'] is None
    assert data['profileUrl'] is None
    assert data['email'] == 'jack@twitter.com'
    assert data['created'] == '2019-02-20T23:11:20.893755'
    assert data['updated'] == '2019-02-20T23:11:20.893755'
