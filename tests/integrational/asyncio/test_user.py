import pytest

from tests.helper import pnconf_obj_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.models.consumer.user import (PNGetUsersResult, PNCreateUserResult, PNGetUserResult,
                                         PNUpdateUserResult, PNDeleteUserResult)
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/user/users_get.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_get_users(event_loop):
    config = pnconf_obj_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.get_users().include('custom').future()
    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetUsersResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 100
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'custom', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'custom', 'created', 'updated', 'eTag']) == set(data[1])


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/user/create_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_create_user(event_loop):
    config = pnconf_obj_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    data = {'id': 'mg', 'name': 'MAGNUM', 'custom': {'XXX': 'YYYY'}}
    envelope = yield from pn.create_user().data(data).include('custom').future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNCreateUserResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert data['id'] == 'mg'
    assert data['name'] == 'MAGNUM'
    assert data['externalId'] is None
    assert data['profileUrl'] is None
    assert data['email'] is None
    assert data['custom'] == {'XXX': 'YYYY'}


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/user/fetch_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_get_user(event_loop):
    config = pnconf_obj_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.get_user().user_id('mg').include('custom').future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetUserResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'created', 'updated', 'eTag', 'custom']) == set(data)
    assert data['id'] == 'mg'
    assert data['name'] == 'MAGNUM'
    assert data['externalId'] is None
    assert data['profileUrl'] is None
    assert data['email'] is None
    assert data['custom'] == {'XXX': 'YYYY'}


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/user/update_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_update_user(event_loop):
    config = pnconf_obj_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.update_user().user_id('mg').data({'name': 'number 3'}).include('custom').future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNUpdateUserResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'created', 'updated', 'eTag', 'custom']) == set(data)
    assert data['id'] == 'mg'
    assert data['name'] == 'number 3'
    assert data['externalId'] is None
    assert data['profileUrl'] is None
    assert data['email'] is None
    assert data['custom'] == {'XXX': 'YYYY'}


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/user/delete_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_delete_user(event_loop):
    config = pnconf_obj_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.delete_user().user_id('mg').future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNDeleteUserResult)
    assert isinstance(envelope.status, PNStatus)
