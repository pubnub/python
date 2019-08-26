import pytest

from tests.helper import pnconf_obj_copy
from tests.integrational.vcr_helper import pn_vcr
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.models.consumer.membership import (PNGetMembersResult, PNGetSpaceMembershipsResult,
                                               PNManageMembersResult, PNManageMembershipsResult)
from pubnub.models.consumer.common import PNStatus


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/members/get_members.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_get_members(event_loop):
    config = pnconf_obj_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.get_members().space_id('value1').include(['custom', 'user', 'user.custom'])\
        .count(True).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetMembersResult)
    assert isinstance(envelope.status, PNStatus)
    assert envelope.result.total_count == 1
    data = envelope.result.data
    assert len(data) == 1
    assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[0])
    assert data[0]['user']['id'] == 'mg3'
    assert data[0]['user']['name'] == 'MAGNUM3'
    assert data[0]['user']['custom'] == {'ZZZ': 'IIII'}


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/members/get_space_memberships.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_get_space_memberships(event_loop):
    config = pnconf_obj_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.get_space_memberships().user_id('mg3').include(['custom', 'space', 'space.custom'])\
        .count(True).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNGetSpaceMembershipsResult)
    assert isinstance(envelope.status, PNStatus)
    assert envelope.result.total_count == 1
    data = envelope.result.data
    assert len(data) == 1
    assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[0])
    assert data[0]['space']['id'] == 'value1'
    assert data[0]['space']['name'] == 'value2'
    assert data[0]['space']['description'] == 'abcd'
    assert data[0]['space']['custom'] is None


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/members/update_space_memberships.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_manage_memberships(event_loop):
    config = pnconf_obj_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.manage_memberships().user_id('mg').data(
        {'add': [{'id': 'value1'}]}).include(['custom', 'space', 'space.custom']).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNManageMembershipsResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 1
    assert set(['id', 'space', 'created', 'updated', 'eTag', 'custom']) == set(data[0])
    assert data[0]['space']['id'] == 'value1'
    assert data[0]['space']['name'] == 'value2'
    assert data[0]['space']['description'] == 'abcd'
    assert data[0]['space']['custom'] is None


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/members/update_members.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
@pytest.mark.asyncio
def test_manage_members(event_loop):
    config = pnconf_obj_copy()
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    envelope = yield from pn.manage_members().space_id('value1').data(
        {'add': [{'id': 'mg3'}]}).include(['custom', 'user', 'user.custom']).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, PNManageMembersResult)
    assert isinstance(envelope.status, PNStatus)
    data = envelope.result.data
    assert len(data) == 2
    assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[0])
    assert set(['user', 'custom', 'id', 'created', 'updated', 'eTag']) == set(data[1])
    if data[0]['user']['id'] == 'mg':
        user = data[0]['user']
    else:
        user = data[1]['user']
    assert user['id'] == 'mg'
    assert user['name'] == 'number 3'
    assert user['custom'] == {'XXX': 'YYYY'}
