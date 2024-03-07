import pytest

from pubnub.pubnub import PubNub
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel import PNRemoveChannelMetadataResult, PNSetChannelMetadataResult, \
    PNGetChannelMetadataResult, PNGetAllChannelMetadataResult
from pubnub.models.consumer.objects_v2.uuid import PNSetUUIDMetadataResult, PNGetUUIDMetadataResult, \
    PNGetAllUUIDMetadataResult, PNRemoveUUIDMetadataResult
from pubnub.structures import Envelope
from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


@pytest.fixture
def pubnub():
    config = pnconf_env_copy()
    config.enable_subscribe = False
    return PubNub(config)


def assert_envelope_of_type(envelope, expected_type):
    assert isinstance(envelope, Envelope)
    assert isinstance(envelope.status, PNStatus)
    assert not envelope.status.is_error()
    assert isinstance(envelope.result, expected_type)


#  Channel metadata

@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/metadata/set_channel_metadata.json',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
def test_set_channel_metadata(pubnub):
    channel = 'metadata_channel'
    set_result = pubnub.set_channel_metadata().channel(channel) \
        .set_name('name') \
        .description('This is a description') \
        .set_status('Testing').set_type('test') \
        .custom({"foo": "bar"}).sync()

    assert_envelope_of_type(set_result, PNSetChannelMetadataResult)
    assert set_result.result.data['id'] == channel
    assert set_result.result.data['name'] == 'name'
    assert set_result.result.data['description'] == 'This is a description'
    assert set_result.result.data['custom'] == {"foo": "bar"}
    assert set_result.result.data['status'] == 'Testing'
    assert set_result.result.data['type'] == 'test'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/metadata/get_channel_metadata.json',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
def test_get_channel_metadata(pubnub):
    channel = 'metadata_channel'
    get_result = pubnub.get_channel_metadata().channel(channel).include_custom(True).sync()
    assert_envelope_of_type(get_result, PNGetChannelMetadataResult)
    assert get_result.result.data['id'] == channel
    assert get_result.result.data['name'] == 'name'
    assert get_result.result.data['description'] == 'This is a description'
    assert get_result.result.data['custom'] == {"foo": "bar"}
    assert get_result.result.data['status'] == 'Testing'
    assert get_result.result.data['type'] == 'test'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/metadata/get_all_channel_metadata.json',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
def test_get_all_channel_metadata(pubnub):
    channel = 'metadata_channel'

    pubnub.set_channel_metadata().channel(f'{channel}-two') \
        .set_name('name') \
        .description('This is a description') \
        .set_status('Testing').set_type('test') \
        .custom({"foo": "bar"}).sync()

    get_all_result = pubnub.get_all_channel_metadata().include_custom(True).sync()
    assert_envelope_of_type(get_all_result, PNGetAllChannelMetadataResult)

    assert len(get_all_result.result.data) == 2
    assert get_all_result.result.data[0]['id'] == channel
    assert get_all_result.result.data[0]['name'] == 'name'
    assert get_all_result.result.data[0]['description'] == 'This is a description'
    assert get_all_result.result.data[0]['custom'] == {"foo": "bar"}
    assert get_all_result.result.data[0]['status'] == 'Testing'
    assert get_all_result.result.data[0]['type'] == 'test'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/metadata/remove_channel_metadata.json',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
def test_remove_channel_metadata(pubnub):
    channel = 'metadata_channel'
    result_1 = pubnub.remove_channel_metadata().channel(channel).sync()
    result_2 = pubnub.remove_channel_metadata().channel(f'{channel}-two').sync()

    get_all_result = pubnub.get_all_channel_metadata().include_custom(True).sync()
    assert_envelope_of_type(result_1, PNRemoveChannelMetadataResult)
    assert_envelope_of_type(result_2, PNRemoveChannelMetadataResult)
    assert_envelope_of_type(get_all_result, PNGetAllChannelMetadataResult)
    assert len(get_all_result.result.data) == 0


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/metadata/set_uuid_metadata.json',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
def test_set_uuid_metadata(pubnub):
    uuid = 'metadata_uuid'
    set_result = pubnub.set_uuid_metadata().uuid(uuid) \
        .set_name('name') \
        .external_id('externalId') \
        .profile_url('https://127.0.0.1') \
        .email('example@127.0.0.1') \
        .set_name('name') \
        .set_type('test') \
        .set_status('Testing') \
        .custom({"foo": "bar"}).sync()

    assert_envelope_of_type(set_result, PNSetUUIDMetadataResult)
    assert set_result.result.data['id'] == uuid
    assert set_result.result.data['name'] == 'name'
    assert set_result.result.data['externalId'] == 'externalId'
    assert set_result.result.data['profileUrl'] == 'https://127.0.0.1'
    assert set_result.result.data['email'] == 'example@127.0.0.1'
    assert set_result.result.data['custom'] == {"foo": "bar"}
    assert set_result.result.data['status'] == 'Testing'
    assert set_result.result.data['type'] == 'test'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/metadata/get_uuid_metadata.json',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
def test_get_uuid_metadata(pubnub):
    uuid = 'metadata_uuid'
    get_result = pubnub.get_uuid_metadata().uuid(uuid).include_custom(True).sync()
    assert_envelope_of_type(get_result, PNGetUUIDMetadataResult)
    assert get_result.result.data['id'] == uuid
    assert get_result.result.data['name'] == 'name'
    assert get_result.result.data['externalId'] == 'externalId'
    assert get_result.result.data['profileUrl'] == 'https://127.0.0.1'
    assert get_result.result.data['email'] == 'example@127.0.0.1'
    assert get_result.result.data['custom'] == {"foo": "bar"}
    assert get_result.result.data['status'] == 'Testing'
    assert get_result.result.data['type'] == 'test'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/metadata/get_all_uuid_metadata.json',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
def test_get_all_uuid_metadata(pubnub):
    uuid = 'metadata_uuid'

    pubnub.set_uuid_metadata().uuid(f'{uuid}-two') \
        .set_name('name') \
        .external_id('externalId') \
        .profile_url('https://127.0.0.1') \
        .email('example@127.0.0.1') \
        .set_name('name') \
        .set_type('test') \
        .set_status('Testing') \
        .custom({"foo": "bar"}).sync()

    get_all_result = pubnub.get_all_uuid_metadata().include_custom(True).sync()
    assert_envelope_of_type(get_all_result, PNGetAllUUIDMetadataResult)
    assert len(get_all_result.result.data) == 2
    assert get_all_result.result.data[0]['id'] == uuid
    assert get_all_result.result.data[0]['name'] == 'name'
    assert get_all_result.result.data[0]['externalId'] == 'externalId'
    assert get_all_result.result.data[0]['profileUrl'] == 'https://127.0.0.1'
    assert get_all_result.result.data[0]['email'] == 'example@127.0.0.1'
    assert get_all_result.result.data[0]['custom'] == {"foo": "bar"}
    assert get_all_result.result.data[0]['status'] == 'Testing'
    assert get_all_result.result.data[0]['type'] == 'test'


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/metadata/remove_uuid_metadata.json',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk'], serializer='pn_json')
def test_remove_uuid_metadata(pubnub):
    uuid = 'metadata_uuid'
    result_1 = pubnub.remove_uuid_metadata().uuid(uuid).sync()
    result_2 = pubnub.remove_uuid_metadata().uuid(f'{uuid}-two').sync()

    get_all_result = pubnub.get_all_uuid_metadata().include_custom(True).sync()
    assert_envelope_of_type(result_2, PNRemoveUUIDMetadataResult)
    assert_envelope_of_type(result_1, PNRemoveUUIDMetadataResult)
    assert_envelope_of_type(get_all_result, PNGetAllUUIDMetadataResult)
    assert len(get_all_result.result.data) == 0
