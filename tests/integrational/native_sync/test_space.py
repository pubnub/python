from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.structures import Envelope
from pubnub.pubnub import PubNub
from pubnub.models.consumer.space import (PNGetSpacesResult, PNCreateSpaceResult, PNGetSpaceResult,
                                          PNUpdateSpaceResult, PNDeleteSpaceResult)
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/get_spaces.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_get_spaces():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.get_spaces().include(['description', 'custom', 'created', 'updated', 'eTag']).sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetSpacesResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 2
    assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[1])


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/create_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_create_space():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.create_space().include({'id': 'my-channel', 'name': 'My space',
                                          'description': 'A space that is mine'}).sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNCreateSpaceResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert data['id'] == 'my-channel'
    assert data['name'] == 'My space'
    assert data['description'] == 'A space that is mine'
    assert data['created'] == '2019-02-20T23:11:20.893755'
    assert data['updated'] == '2019-02-20T23:11:20.893755'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/get_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_get_space():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.get_space().space_id(
        'my-chanel').include(['description', 'name', 'created', 'updated', 'eTag']).sync()

    assert(isinstance(envelope, Envelope))
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


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/update_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_update_space():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.update_space().space_id('my-channel').include({'id': 'my-channel', 'name': 'My space',
                                                                 'description': 'A space that is mine'}).sync()

    assert(isinstance(envelope, Envelope))
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


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/space/delete_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
def test_delete_space():
    config = pnconf_copy()
    pn = PubNub(config)
    envelope = pn.delete_space().space_id('main').sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNDeleteSpaceResult)
    assert isinstance(envelope.status, PNStatus)
    assert envelope.result.data == {}
