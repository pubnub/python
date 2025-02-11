import pytest

from pubnub.endpoints.endpoint import Endpoint
from pubnub.endpoints.objects_v2.uuid.get_all_uuid import GetAllUuid
from pubnub.endpoints.objects_v2.uuid.get_uuid import GetUuid
from pubnub.endpoints.objects_v2.uuid.remove_uuid import RemoveUuid
from pubnub.endpoints.objects_v2.uuid.set_uuid import SetUuid
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
from pubnub.models.consumer.objects_v2.uuid import PNSetUUIDMetadataResult, PNGetUUIDMetadataResult, \
    PNRemoveUUIDMetadataResult, PNGetAllUUIDMetadataResult
from pubnub.pubnub_asyncio import PubNubAsyncio
from pubnub.models.envelopes import AsyncioEnvelope
from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


class TestObjectsV2UUID:
    _some_uuid = "someuuid"
    _some_name = "Some name"
    _some_email = "test@example.com"
    _some_profile_url = "http://example.com"
    _some_external_id = "1234"
    _some_custom = {
        "key1": "val1",
        "key2": "val2"
    }

    def test_set_uuid_endpoint_available(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)
        set_uuid = pn.set_uuid_metadata()
        assert set_uuid is not None
        assert isinstance(set_uuid, SetUuid)
        assert isinstance(set_uuid, Endpoint)

    def test_set_uuid_is_endpoint(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)
        set_uuid = pn.set_uuid_metadata()
        assert isinstance(set_uuid, SetUuid)
        assert isinstance(set_uuid, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/uuid/set_uuid.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_set_uuid_happy_path(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)

        set_uuid_result = await pn.set_uuid_metadata() \
            .include_custom(True) \
            .uuid(TestObjectsV2UUID._some_uuid) \
            .set_name(TestObjectsV2UUID._some_name) \
            .email(TestObjectsV2UUID._some_email) \
            .profile_url(TestObjectsV2UUID._some_profile_url) \
            .external_id(TestObjectsV2UUID._some_external_id) \
            .custom(TestObjectsV2UUID._some_custom) \
            .future()

        assert isinstance(set_uuid_result, AsyncioEnvelope)
        assert isinstance(set_uuid_result.result, PNSetUUIDMetadataResult)
        assert isinstance(set_uuid_result.status, PNStatus)
        data = set_uuid_result.result.data
        assert data['id'] == TestObjectsV2UUID._some_uuid
        assert data['name'] == TestObjectsV2UUID._some_name
        assert data['externalId'] == TestObjectsV2UUID._some_external_id
        assert data['profileUrl'] == TestObjectsV2UUID._some_profile_url
        assert data['email'] == TestObjectsV2UUID._some_email
        assert data['custom'] == TestObjectsV2UUID._some_custom

    def test_get_uuid_endpoint_available(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)
        get_uuid = pn.get_uuid_metadata()
        assert get_uuid is not None
        assert isinstance(get_uuid, GetUuid)
        assert isinstance(get_uuid, Endpoint)

    def test_get_uuid_is_endpoint(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)
        get_uuid = pn.get_uuid_metadata()
        assert isinstance(get_uuid, GetUuid)
        assert isinstance(get_uuid, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/uuid/get_uuid.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_get_uuid_happy_path(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)

        get_uuid_result = await pn.get_uuid_metadata() \
            .include_custom(True) \
            .uuid(TestObjectsV2UUID._some_uuid) \
            .future()

        assert isinstance(get_uuid_result, AsyncioEnvelope)
        assert isinstance(get_uuid_result.result, PNGetUUIDMetadataResult)
        assert isinstance(get_uuid_result.status, PNStatus)
        data = get_uuid_result.result.data
        assert data['id'] == TestObjectsV2UUID._some_uuid
        assert data['name'] == TestObjectsV2UUID._some_name
        assert data['externalId'] == TestObjectsV2UUID._some_external_id
        assert data['profileUrl'] == TestObjectsV2UUID._some_profile_url
        assert data['email'] == TestObjectsV2UUID._some_email
        assert data['custom'] == TestObjectsV2UUID._some_custom

    def test_remove_uuid_endpoint_available(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)
        remove_uuid = pn.remove_uuid_metadata()
        assert remove_uuid is not None
        assert isinstance(remove_uuid, RemoveUuid)
        assert isinstance(remove_uuid, Endpoint)

    def test_remove_uuid_is_endpoint(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)
        remove_uuid = pn.remove_uuid_metadata()
        assert isinstance(remove_uuid, RemoveUuid)
        assert isinstance(remove_uuid, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/uuid/remove_uuid.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_remove_uuid_happy_path(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)

        remove_uid_result = await pn.remove_uuid_metadata() \
            .uuid(TestObjectsV2UUID._some_uuid) \
            .future()

        assert isinstance(remove_uid_result, AsyncioEnvelope)
        assert isinstance(remove_uid_result.result, PNRemoveUUIDMetadataResult)
        assert isinstance(remove_uid_result.status, PNStatus)

    def test_get_all_uuid_endpoint_available(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)
        get_all_uuid = pn.get_all_uuid_metadata()
        assert get_all_uuid is not None
        assert isinstance(get_all_uuid, GetAllUuid)
        assert isinstance(get_all_uuid, Endpoint)

    def test_get_all_uuid_is_endpoint(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)
        get_all_uuid = pn.get_all_uuid_metadata()
        assert isinstance(get_all_uuid, GetAllUuid)
        assert isinstance(get_all_uuid, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/uuid/get_all_uuid.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_get_all_uuid_happy_path(self):
        config = pnconf_env_copy()
        pn = PubNubAsyncio(config)

        get_all_uuid_result = await pn.get_all_uuid_metadata() \
            .include_custom(True) \
            .limit(10) \
            .include_total_count(True) \
            .sort(PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)) \
            .page(None) \
            .future()

        assert isinstance(get_all_uuid_result, AsyncioEnvelope)
        assert isinstance(get_all_uuid_result.result, PNGetAllUUIDMetadataResult)
        assert isinstance(get_all_uuid_result.status, PNStatus)
        data = get_all_uuid_result.result.data
        assert isinstance(data, list)
        assert get_all_uuid_result.result.total_count != 0
        assert get_all_uuid_result.result.next is not None
        assert get_all_uuid_result.result.prev is None

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/uuid/if_matches_etag.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_if_matches_etag(self):
        config = pnconf_env_copy()
        pubnub = PubNubAsyncio(config)

        set_uuid = await pubnub.set_uuid_metadata(uuid=self._some_uuid, name=self._some_name).future()
        original_etag = set_uuid.result.data.get('eTag')
        get_uuid = await pubnub.get_uuid_metadata(uuid=self._some_uuid).future()
        assert original_etag == get_uuid.result.data.get('eTag')

        # Update without eTag should be possible
        set_uuid = await pubnub.set_uuid_metadata(uuid=self._some_uuid, name=f"{self._some_name}-2").future()

        # Response should contain new eTag
        new_etag = set_uuid.result.data.get('eTag')
        assert original_etag != new_etag
        assert set_uuid.result.data.get('name') == f"{self._some_name}-2"

        get_uuid = await pubnub.get_uuid_metadata(uuid=self._some_uuid).future()
        assert original_etag != get_uuid.result.data.get('eTag')
        assert get_uuid.result.data.get('name') == f"{self._some_name}-2"

        # Update with correct eTag should be possible
        set_uuid = await pubnub.set_uuid_metadata(uuid=self._some_uuid, name=f"{self._some_name}-3") \
            .if_matches_etag(new_etag) \
            .future()
        assert set_uuid.result.data.get('name') == f"{self._some_name}-3"

        try:
            # Update with original - now outdated - eTag should fail
            set_uuid = await pubnub.set_uuid_metadata(uuid=self._some_uuid, name=f"{self._some_name}-3") \
                .if_matches_etag(original_etag) \
                .future()
        except PubNubException as e:
            assert e.get_status_code() == 412
            assert e.get_error_message().get('message') == 'User to update has been modified after it was read.'
