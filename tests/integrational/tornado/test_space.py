import tornado
from tornado.testing import AsyncTestCase

from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope
from pubnub.models.consumer.space import (PNGetSpacesResult, PNCreateSpaceResult, PNGetSpaceResult,
                                          PNUpdateSpaceResult, PNDeleteSpaceResult)
from pubnub.models.consumer.common import PNStatus


class TestSpace(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        config = pnconf_copy()
        self.pn = PubNubTornado(config, custom_ioloop=self.io_loop)

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/get_spaces.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_get_spaces(self):
        envelope = yield self.pn.get_spaces().include(['description', 'custom', 'created', 'updated', 'eTag']).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNGetSpacesResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert len(data) == 2
        assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[0])
        assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[1])
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/create_space.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_create_space(self):
        envelope = yield self.pn.create_space().include({'id': 'my-channel', 'name': 'My space',
                                                         'description': 'A space that is mine'}).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNCreateSpaceResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert data['id'] == 'my-channel'
        assert data['name'] == 'My space'
        assert data['description'] == 'A space that is mine'
        assert data['created'] == '2019-02-20T23:11:20.893755'
        assert data['updated'] == '2019-02-20T23:11:20.893755'
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/get_space.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_get_space(self):
        envelope = yield self.pn.get_space().space_id(
            'my-chanel').include(['description', 'name', 'created', 'updated', 'eTag']).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNGetSpaceResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert set(['name', 'id', 'description', 'created', 'updated', 'eTag']) == set(data)
        assert data['id'] == 'my-channel'
        assert data['name'] == 'My space'
        assert data['description'] == 'A space that is mine'
        assert data['created'] == '2019-02-20T23:11:20.893755'
        assert data['updated'] == '2019-02-20T23:11:20.893755'
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/update_space.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_update_space(self):
        include = {'id': 'my-channel', 'name': 'My space',
                   'description': 'A space that is mine'}
        envelope = yield self.pn.update_space().space_id('my-channel').include(include).future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNUpdateSpaceResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert set(['name', 'id', 'description', 'created', 'updated', 'eTag']) == set(data)
        assert data['id'] == 'my-channel'
        assert data['name'] == 'My space'
        assert data['description'] == 'A space that is mine'
        assert data['created'] == '2019-02-20T23:11:20.893755'
        assert data['updated'] == '2019-02-20T23:11:20.893755'
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/delete_space.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_delete_space(self):
        envelope = yield self.pn.delete_space().space_id('main').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNDeleteSpaceResult)
        assert isinstance(envelope.status, PNStatus)
        assert envelope.result.data == {}
        self.pn.stop()
