from tests.helper import pnconf_obj_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.structures import Envelope
from pubnub.pubnub import PubNub
from pubnub.models.consumer.user import (PNGetUsersResult, PNCreateUserResult, PNGetUserResult,
                                         PNUpdateUserResult, PNDeleteUserResult)
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/users_get.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_get_users():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.get_users().include('custom').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetUsersResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 100
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'custom', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'custom', 'created', 'updated', 'eTag']) == set(data[1])


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/create_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_create_user():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.create_user().data({'id': 'mg', 'name': 'MAGNUM', 'custom': {
        'XXX': 'YYYY'}}).include('custom').sync()

    assert(isinstance(envelope, Envelope))
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


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/fetch_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_get_user():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.get_user().user_id('mg').include('custom').sync()

    assert(isinstance(envelope, Envelope))
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


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/update_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_update_user():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.update_user().user_id('mg').data({'name': 'number 3'}).include('custom').sync()

    assert(isinstance(envelope, Envelope))
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


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/delete_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_delete_user():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.delete_user().user_id('mg').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNDeleteUserResult)
    assert isinstance(envelope.status, PNStatus)
