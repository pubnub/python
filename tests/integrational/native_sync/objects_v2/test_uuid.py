from pubnub.endpoints.endpoint import Endpoint
from pubnub.endpoints.objects_v2.uuid.get_all_uuid import GetAllUuid
from pubnub.endpoints.objects_v2.uuid.get_uuid import GetUuid
from pubnub.endpoints.objects_v2.uuid.remove_uuid import RemoveUuid
from pubnub.endpoints.objects_v2.uuid.set_uuid import SetUuid
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
from pubnub.models.consumer.objects_v2.uuid import PNSetUUIDMetadataResult, PNGetUUIDMetadataResult, \
    PNRemoveUUIDMetadataResult, PNGetAllUUIDMetadataResult
from pubnub.pubnub import PubNub
from pubnub.structures import Envelope
from tests.helper import pnconf_copy
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
        config = pnconf_copy()
        pn = PubNub(config)
        set_uuid = pn.set_uuid_metadata()
        assert set_uuid is not None
        assert isinstance(set_uuid, SetUuid)
        assert isinstance(set_uuid, Endpoint)

    def test_set_uuid_is_endpoint(self):
        config = pnconf_copy()
        pn = PubNub(config)
        set_uuid = pn.set_uuid_metadata()
        assert isinstance(set_uuid, SetUuid)
        assert isinstance(set_uuid, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/uuid/set_uuid.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_set_uuid_happy_path(self):
        config = pnconf_copy()
        pn = PubNub(config)

        set_uuid_result = pn.set_uuid_metadata() \
            .include_custom(True) \
            .uuid(TestObjectsV2UUID._some_uuid) \
            .set_name(TestObjectsV2UUID._some_name) \
            .email(TestObjectsV2UUID._some_email) \
            .profile_url(TestObjectsV2UUID._some_profile_url) \
            .external_id(TestObjectsV2UUID._some_external_id) \
            .custom(TestObjectsV2UUID._some_custom) \
            .sync()

        assert isinstance(set_uuid_result, Envelope)
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
        config = pnconf_copy()
        pn = PubNub(config)
        get_uuid = pn.get_uuid_metadata()
        assert get_uuid is not None
        assert isinstance(get_uuid, GetUuid)
        assert isinstance(get_uuid, Endpoint)

    def test_get_uuid_is_endpoint(self):
        config = pnconf_copy()
        pn = PubNub(config)
        get_uuid = pn.get_uuid_metadata()
        assert isinstance(get_uuid, GetUuid)
        assert isinstance(get_uuid, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/uuid/get_uuid.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_get_uuid_happy_path(self):
        config = pnconf_copy()
        pn = PubNub(config)

        get_uuid_result = pn.get_uuid_metadata() \
            .include_custom(True) \
            .uuid(TestObjectsV2UUID._some_uuid) \
            .sync()

        assert isinstance(get_uuid_result, Envelope)
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
        config = pnconf_copy()
        pn = PubNub(config)
        remove_uuid = pn.remove_uuid_metadata()
        assert remove_uuid is not None
        assert isinstance(remove_uuid, RemoveUuid)
        assert isinstance(remove_uuid, Endpoint)

    def test_remove_uuid_is_endpoint(self):
        config = pnconf_copy()
        pn = PubNub(config)
        remove_uuid = pn.remove_uuid_metadata()
        assert isinstance(remove_uuid, RemoveUuid)
        assert isinstance(remove_uuid, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/uuid/remove_uuid.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_remove_uuid_happy_path(self):
        config = pnconf_copy()
        pn = PubNub(config)

        remove_uid_result = pn.remove_uuid_metadata() \
            .uuid(TestObjectsV2UUID._some_uuid) \
            .sync()

        assert isinstance(remove_uid_result, Envelope)
        assert isinstance(remove_uid_result.result, PNRemoveUUIDMetadataResult)
        assert isinstance(remove_uid_result.status, PNStatus)

    def test_get_all_uuid_endpoint_available(self):
        config = pnconf_copy()
        pn = PubNub(config)
        get_all_uuid = pn.get_all_uuid_metadata()
        assert get_all_uuid is not None
        assert isinstance(get_all_uuid, GetAllUuid)
        assert isinstance(get_all_uuid, Endpoint)

    def test_get_all_uuid_is_endpoint(self):
        config = pnconf_copy()
        pn = PubNub(config)
        get_all_uuid = pn.get_all_uuid_metadata()
        assert isinstance(get_all_uuid, GetAllUuid)
        assert isinstance(get_all_uuid, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/uuid/get_all_uuid.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_get_all_uuid_happy_path(self):
        config = pnconf_copy()
        pn = PubNub(config)

        get_all_uuid_result = pn.get_all_uuid_metadata() \
            .include_custom(True) \
            .limit(10) \
            .include_total_count(True) \
            .sort(PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)) \
            .page(None) \
            .sync()

        assert isinstance(get_all_uuid_result, Envelope)
        assert isinstance(get_all_uuid_result.result, PNGetAllUUIDMetadataResult)
        assert isinstance(get_all_uuid_result.status, PNStatus)
        data = get_all_uuid_result.result.data
        assert isinstance(data, list)
        assert get_all_uuid_result.result.total_count != 0
        assert get_all_uuid_result.result.next is not None
        assert get_all_uuid_result.result.prev is None
