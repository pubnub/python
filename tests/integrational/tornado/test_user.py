import tornado
from tornado.testing import AsyncTestCase

from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope
from pubnub.models.consumer.user import (PNGetUsersResult, PNCreateUserResult, PNGetUserResult,
                                         PNUpdateUserResult, PNDeleteUserResult)
from pubnub.models.consumer.common import PNStatus
from tests.helper import pnconf_obj_copy
from tests.integrational.vcr_helper import pn_vcr


class TestUser(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        config = pnconf_obj_copy()
        self.pn = PubNubTornado(config, custom_ioloop=self.io_loop)

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/users_get.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_get_users(self):
        envelope = yield self.pn.get_users().include('custom').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNGetUsersResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert len(data) == 100
        assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                    'custom', 'created', 'updated', 'eTag']) == set(data[0])
        assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                    'custom', 'created', 'updated', 'eTag']) == set(data[1])
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/create_user.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_create_user(self):
        data = {'id': 'mg', 'name': 'MAGNUM', 'custom': {'XXX': 'YYYY'}}
        envelope = yield self.pn.create_user().data(data).include('custom').future()

        assert(isinstance(envelope, TornadoEnvelope))
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
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/fetch_user.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_get_user(self):
        envelope = yield self.pn.get_user().user_id('mg').include('custom').future()

        assert(isinstance(envelope, TornadoEnvelope))
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
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/update_user.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_update_user(self):
        envelope = yield self.pn.update_user().user_id('mg').data({'name': 'number 3'}).include('custom').future()

        assert(isinstance(envelope, TornadoEnvelope))
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
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/delete_user.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_delete_user(self):
        envelope = yield self.pn.delete_user().user_id('mg').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNDeleteUserResult)
        assert isinstance(envelope.status, PNStatus)
        self.pn.stop()
