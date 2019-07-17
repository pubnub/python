import tornado
from tornado.testing import AsyncTestCase

from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope
from pubnub.models.consumer.user import (PNGetUsersResult, PNCreateUserResult, PNFetchUserResult,
                                         PNUpdateUserResult, PNDeleteUserResult)
from pubnub.models.consumer.common import PNStatus
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


class TestGetUsers(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        config = pnconf_copy()
        self.pn = PubNubTornado(config, custom_ioloop=self.io_loop)

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/users_get.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_single_channel(self):
        envelope = yield self.pn.get_users().include(['externalId', 'profileUrl', 'email',
                                                      'custom', 'created', 'updated', 'eTag']).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNGetUsersResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert len(data) == 2
        assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                    'custom', 'created', 'updated', 'eTag']) == set(data[0])
        assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                    'custom', 'created', 'updated', 'eTag']) == set(data[1])
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/create_user.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_create_user(self):
        data = {'id': 'user-1', 'name': 'John Doe',
                'externalId': None, 'profileUrl': None, 'email': 'jack@twitter.com'}
        envelope = yield self.pn.create_user().include(data).future()

        assert(isinstance(envelope, TornadoEnvelope))
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
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/fetch_user.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_fetch_user(self):
        envelope = yield self.pn.fetch_user().user_id('user-1').include(['externalId', 'profileUrl', 'email',
                                                                         'created', 'updated', 'eTag']).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNFetchUserResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                    'created', 'updated', 'eTag']) == set(data)
        assert data['id'] == 'user-1'
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/update_user.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_update_user(self):
        envelope = yield self.pn.update_user().user_id('user-1').include({'id': 'user-1', 'name': 'John Doe',
                                                                          'externalId': None, 'profileUrl': None,
                                                                          'email': 'jack@twitter.com'}).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNUpdateUserResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert set(['name', 'id', 'externalId', 'profileUrl', 'email',
                    'created', 'updated', 'eTag']) == set(data)
        assert data['id'] == 'user-1'
        assert data['name'] == 'John Doe'
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/user/delete_user.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_delete_user(self):
        envelope = yield self.pn.delete_user().user_id('user-1').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNDeleteUserResult)
        assert isinstance(envelope.status, PNStatus)
        assert envelope.result.data == {}
        self.pn.stop()
