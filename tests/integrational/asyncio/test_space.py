import pytest

from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.models.consumer.space import (PNGetSpacesResult, PNCreateSpaceResult, PNGetSpaceResult,
                                          PNUpdateSpaceResult, PNDeleteSpaceResult)
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/space/get_spaces.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_get_spaces(event_loop):
    config = pnconf_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.get_spaces().include(['description', 'custom', 'created', 'updated', 'eTag']).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetSpacesResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 2
    assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['name', 'id', 'description', 'custom', 'created', 'updated', 'eTag']) == set(data[1])


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/space/create_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_create_space(event_loop):
    config = pnconf_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.create_space().include({'id': 'my-channel', 'name': 'My space',
                                                     'description': 'A space that is mine'}).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNCreateSpaceResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert data['id'] == 'my-channel'
    assert data['name'] == 'My space'
    assert data['description'] == 'A space that is mine'
    assert data['created'] == '2019-02-20T23:11:20.893755'
    assert data['updated'] == '2019-02-20T23:11:20.893755'


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/space/get_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_get_space(event_loop):
    config = pnconf_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.get_space().space_id(
        'my-chanel').include(['description', 'name', 'created', 'updated', 'eTag']).future()

    assert(isinstance(envelope, AsyncioEnvelope))
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


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/space/update_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_update_space(event_loop):
    config = pnconf_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    include = {'id': 'my-channel', 'name': 'My space',
               'description': 'A space that is mine'}
    envelope = yield from pn.update_space().space_id('my-channel').include(include).future()

    assert(isinstance(envelope, AsyncioEnvelope))
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


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/space/delete_space.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_delete_space(event_loop):
    config = pnconf_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.delete_space().space_id('main').future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNDeleteSpaceResult)
    assert isinstance(envelope.status, PNStatus)
    assert envelope.result.data == {}
