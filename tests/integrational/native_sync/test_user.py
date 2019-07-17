from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.structures import Envelope
from pubnub.pubnub import PubNub
from pubnub.models.consumer.user import (PNGetUsersResult, PNCreateUserResult, PNFetchUserResult,
                                         PNUpdateUserResult, PNDeleteUserResult)
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


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/create_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_create_user():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.create_user().include({'id': 'user-1', 'name': 'John Doe',
                                         'externalId': None, 'profileUrl': None, 'email': 'jack@twitter.com'}).sync()

    assert(isinstance(envelope, Envelope))
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


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/fetch_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_fetch_user():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.fetch_user().user_id('user-1').include(['externalId', 'profileUrl', 'email',
                                                          'created', 'updated', 'eTag']).sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNFetchUserResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'created', 'updated', 'eTag']) == set(data)
    assert data['id'] == 'user-1'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/update_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_update_user():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.update_user().user_id('user-1').include({'id': 'user-1', 'name': 'John Doe',
                                                           'externalId': None, 'profileUrl': None,
                                                           'email': 'jack@twitter.com'}).sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNUpdateUserResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                'created', 'updated', 'eTag']) == set(data)
    assert data['id'] == 'user-1'
    assert data['name'] == 'John Doe'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/user/delete_user.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_delete_user():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.delete_user().user_id('user-1').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNDeleteUserResult)
    assert isinstance(envelope.status, PNStatus)
    assert envelope.result.data == {}
