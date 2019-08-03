import tornado
from tornado.testing import AsyncTestCase

from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope
from pubnub.models.consumer.membership import (PNGetMembersResult, PNGetSpaceMembershipsResult,
                                               PNUpdateSpaceMembershipsResult, PNUpdateMembersResult)
from pubnub.models.consumer.common import PNStatus
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


class TestUser(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        config = pnconf_copy()
        self.pn = PubNubTornado(config, custom_ioloop=self.io_loop)

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/members/get_members.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_get_members(self):
        envelope = yield self.pn.get_members().space_id('main').limit(10).count(True)\
            .include(['custom', 'user']).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNGetMembersResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert len(data) == 2
        assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[0])
        assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[1])
        assert data[0]['user']['id'] == 'user-1'
        assert data[0]['user']['name'] == 'John Doe'
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/members/get_space_memberships.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_get_space_memberships(self):
        envelope = yield self.pn.get_space_memberships().user_id('charlie').limit(10).count(True)\
            .include(['custom', 'space']).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNGetSpaceMembershipsResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert len(data) == 2
        assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[0])
        assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[1])
        assert data[0]['space']['id'] == 'my-channel'
        assert data[0]['space']['name'] == 'My space'
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/members/update_space_memberships.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_update_space_memberships(self):
        data = {
            "add": [
                {
                    "id": "my-channel"
                }
            ],
            "update": [
                {
                    "id": "main",
                    "custom": {
                        "starred": True
                    }
                }
            ],
            "remove": [
                {
                    "id": "space-0"
                }
            ]
        }
        envelope = yield self.pn.update_space_memberships().user_id('charlie').limit(10).count(True)\
            .include('custom').data(data).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNUpdateSpaceMembershipsResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert len(data) == 2
        assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[0])
        assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[1])
        assert data[0]['space']['id'] == 'my-channel'
        assert data[0]['space']['name'] == 'My space'
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/members/update_members.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_update_members(self):
        data = {
            "add": [
                {
                    "id": "user-1"
                }
            ],
            "update": [
                {
                    "id": "user-2",
                    "custom": {
                        "role": "moderator"
                    }
                }
            ],
            "remove": [
                {
                    "id": "user-0"
                }
            ]
        }
        envelope = yield self.pn.update_members().space_id('main').limit(10).count(True).include('custom')\
            .data(data).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNUpdateMembersResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert len(data) == 2
        assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[0])
        assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[1])
        assert data[0]['user']['id'] == 'user-1'
        assert data[0]['user']['name'] == 'John Doe'
        self.pn.stop()
