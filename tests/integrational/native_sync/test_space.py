from tests.helper import pnconf_obj_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.structures import Envelope
from pubnub.pubnub import PubNub
from pubnub.models.consumer.space import (PNGetSpacesResult, PNCreateSpaceResult, PNGetSpaceResult,
                                          PNUpdateSpaceResult, PNDeleteSpaceResult)
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/get_spaces.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_get_spaces():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.get_spaces().include('custom').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetSpacesResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 100
    assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[1])


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/create_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_create_space():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.create_space().data({'id': 'in_space', 'name': 'some_name',
                                       'custom': {'a': 3}}).include('custom').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNCreateSpaceResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert data['id'] == 'in_space'
    assert data['name'] == 'some_name'
    assert data['custom'] == {'a': 3}
    assert data['description'] is None


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/get_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_get_space():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.get_space().space_id('in_space').include('custom').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetSpaceResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert set(['name', 'id', 'description', 'created', 'updated', 'eTag', 'custom']) == set(data)
    assert data['id'] == 'in_space'
    assert data['name'] == 'some_name'
    assert data['custom'] == {'a': 3}
    assert data['description'] is None


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/update_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_update_space():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.update_space().space_id('in_space').data({'description': 'desc'}).include('custom').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNUpdateSpaceResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert set(['name', 'id', 'description', 'created', 'updated', 'eTag', 'custom']) == set(data)
    assert data['id'] == 'in_space'
    assert data['name'] == 'some_name'
    assert data['custom'] == {'a': 3}
    assert data['description'] == 'desc'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/delete_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_delete_space():
    config = pnconf_obj_copy()
    pn = PubNub(config)
    envelope = pn.delete_space().space_id('in_space').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNDeleteSpaceResult)
    assert isinstance(envelope.status, PNStatus)
