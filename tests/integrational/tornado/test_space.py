import tornado
from tornado.testing import AsyncTestCase

from tests.helper import pnconf_obj_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope
from pubnub.models.consumer.space import (PNGetSpacesResult, PNCreateSpaceResult, PNGetSpaceResult,
                                          PNUpdateSpaceResult, PNDeleteSpaceResult)
from pubnub.models.consumer.common import PNStatus


class TestSpace(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        config = pnconf_obj_copy()
        self.pn = PubNubTornado(config, custom_ioloop=self.io_loop)

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/get_spaces.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_get_spaces(self):
        envelope = yield self.pn.get_spaces().include('custom').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNGetSpacesResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert len(data) == 100
        assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[0])
        assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[1])
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/create_space.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_create_space(self):
        envelope = yield self.pn.create_space().data({'id': 'in_space', 'name': 'some_name',
                                                      'custom': {'a': 3}}).include('custom').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNCreateSpaceResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert data['id'] == 'in_space'
        assert data['name'] == 'some_name'
        assert data['custom'] == {'a': 3}
        assert data['description'] is None
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/get_space.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_get_space(self):
        envelope = yield self.pn.get_space().space_id('in_space').include('custom').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNGetSpaceResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert set(['name', 'id', 'description', 'created', 'updated', 'eTag', 'custom']) == set(data)
        assert data['id'] == 'in_space'
        assert data['name'] == 'some_name'
        assert data['custom'] == {'a': 3}
        assert data['description'] is None
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/update_space.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_update_space(self):
        data = {'description': 'desc'}
        envelope = yield self.pn.update_space().space_id('in_space').data(data).include('custom').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNUpdateSpaceResult)
        assert isinstance(envelope.status, PNStatus)
        data = envelope.result.data
        assert set(['name', 'id', 'description', 'created', 'updated', 'eTag', 'custom']) == set(data)
        assert data['id'] == 'in_space'
        assert data['name'] == 'some_name'
        assert data['custom'] == {'a': 3}
        assert data['description'] == 'desc'
        self.pn.stop()

    @pn_vcr.use_cassette('tests/integrational/fixtures/tornado/space/delete_space.yaml',
                         filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_delete_space(self):
        envelope = yield self.pn.delete_space().space_id('in_space').future()

        assert(isinstance(envelope, TornadoEnvelope))
        assert not envelope.status.is_error()
        assert isinstance(envelope.result, PNDeleteSpaceResult)
        assert isinstance(envelope.status, PNStatus)
        self.pn.stop()
