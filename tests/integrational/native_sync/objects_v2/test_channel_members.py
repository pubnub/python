from pubnub.endpoints.endpoint import Endpoint
from pubnub.endpoints.objects_v2.objects_endpoint import UUIDIncludeEndpoint
from pubnub.endpoints.objects_v2.members.get_channel_members import GetChannelMembers
from pubnub.endpoints.objects_v2.members.manage_channel_members import ManageChannelMembers
from pubnub.endpoints.objects_v2.members.remove_channel_members import RemoveChannelMembers
from pubnub.endpoints.objects_v2.members.set_channel_members import SetChannelMembers
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel_members import PNUUID, JustUUID, PNSetChannelMembersResult, \
    PNGetChannelMembersResult, PNRemoveChannelMembersResult, PNManageChannelMembersResult
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.pubnub import PubNub
from pubnub.structures import Envelope
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


def _pubnub():
    config = pnconf_copy()
    return PubNub(config)


class TestObjectsV2ChannelMembers:
    _some_channel_id = "somechannelid"

    def test_set_channel_members_endpoint_available(self):
        pn = _pubnub()
        set_channel_members = pn.set_channel_members()
        assert set_channel_members is not None

    def test_set_channel_members_is_endpoint(self):
        pn = _pubnub()
        set_channel_members = pn.set_channel_members()
        assert isinstance(set_channel_members, SetChannelMembers)
        assert isinstance(set_channel_members, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel_members/set_channel_members.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_set_channel_members_happy_path(self):
        pn = _pubnub()

        some_uuid = "someuuid"
        some_uuid_with_custom = "someuuid_with_custom"

        pn.set_uuid_metadata()\
            .uuid(some_uuid)\
            .set_name("some name")\
            .sync()

        custom_1 = {
            "key3": "val1",
            "key4": "val2"}
        pn.set_uuid_metadata() \
            .uuid(some_uuid_with_custom) \
            .set_name("some name with custom") \
            .custom(custom_1) \
            .sync()

        custom_2 = {
            "key5": "val1",
            "key6": "val2"
        }
        uuids_to_set = [
            PNUUID.uuid(some_uuid),
            PNUUID.uuid_with_custom(some_uuid_with_custom, custom_2)
        ]

        set_channel_members_result = pn.set_channel_members()\
            .channel(TestObjectsV2ChannelMembers._some_channel_id)\
            .uuids(uuids_to_set)\
            .include_custom(True)\
            .include_uuid(UUIDIncludeEndpoint.UUID_WITH_CUSTOM)\
            .sync()

        assert isinstance(set_channel_members_result, Envelope)
        assert isinstance(set_channel_members_result.result, PNSetChannelMembersResult)
        assert isinstance(set_channel_members_result.status, PNStatus)
        assert not set_channel_members_result.status.is_error()
        data = set_channel_members_result.result.data
        assert isinstance(data, list)

        assert len([e for e in data if e['uuid']['id'] == some_uuid or e['uuid']['id'] == some_uuid_with_custom]) == 2
        assert len([e for e in data if e['uuid']['custom'] == custom_1]) != 0
        assert len([e for e in data if e['custom'] == custom_2]) != 0

    def test_get_channel_members_endpoint_available(self):
        pn = _pubnub()
        get_channel_members = pn.get_channel_members()
        assert get_channel_members is not None

    def test_get_channel_members_is_endpoint(self):
        pn = _pubnub()
        get_channel_members = pn.get_channel_members()
        assert isinstance(get_channel_members, GetChannelMembers)
        assert isinstance(get_channel_members, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel_members/get_channel_members.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_get_channel_members_happy_path(self):
        pn = _pubnub()

        some_uuid = "someuuid"
        some_uuid_with_custom = "someuuid_with_custom"

        custom_1 = {
            "key3": "val1",
            "key4": "val2"}
        pn.set_uuid_metadata() \
            .uuid(some_uuid_with_custom) \
            .set_name("some name with custom") \
            .custom(custom_1) \
            .sync()

        custom_2 = {
            "key5": "val1",
            "key6": "val2"
        }

        get_channel_members_result = pn.get_channel_members()\
            .channel(TestObjectsV2ChannelMembers._some_channel_id)\
            .include_custom(True)\
            .include_uuid(UUIDIncludeEndpoint.UUID_WITH_CUSTOM)\
            .sync()

        assert isinstance(get_channel_members_result, Envelope)
        assert isinstance(get_channel_members_result.result, PNGetChannelMembersResult)
        assert isinstance(get_channel_members_result.status, PNStatus)
        assert not get_channel_members_result.status.is_error()
        data = get_channel_members_result.result.data
        assert isinstance(data, list)

        assert len([e for e in data if e['uuid']['id'] == some_uuid or e['uuid']['id'] == some_uuid_with_custom]) == 2
        assert len([e for e in data if e['uuid']['custom'] == custom_1]) != 0
        assert len([e for e in data if e['custom'] == custom_2]) != 0

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/objects_v2/channel_members/get_channel_members_with_pagination.yaml',
        filter_query_parameters=['uuid', 'pnsdk'])
    def test_get_channel_members_with_pagination(self):
        pn = _pubnub()

        pn.set_channel_members().channel(TestObjectsV2ChannelMembers._some_channel_id) \
            .uuids([JustUUID(f'test-fix-118-{x}') for x in range(15)]) \
            .sync()

        get_channel_members_result_page_1 = pn.get_channel_members()\
            .channel(TestObjectsV2ChannelMembers._some_channel_id)\
            .limit(10) \
            .sync()

        assert isinstance(get_channel_members_result_page_1, Envelope)
        assert isinstance(get_channel_members_result_page_1.result, PNGetChannelMembersResult)
        assert isinstance(get_channel_members_result_page_1.status, PNStatus)
        assert isinstance(get_channel_members_result_page_1.result.next, PNPage)

        assert not get_channel_members_result_page_1.status.is_error()
        data = get_channel_members_result_page_1.result.data
        assert len(data) == 10

        get_channel_members_result_page_2 = pn.get_channel_members() \
            .channel(TestObjectsV2ChannelMembers._some_channel_id) \
            .limit(10) \
            .page(get_channel_members_result_page_1.result.next) \
            .sync()

        assert isinstance(get_channel_members_result_page_2, Envelope)
        assert isinstance(get_channel_members_result_page_2.result, PNGetChannelMembersResult)
        assert isinstance(get_channel_members_result_page_2.status, PNStatus)
        assert isinstance(get_channel_members_result_page_2.result.next, PNPage)

        assert not get_channel_members_result_page_2.status.is_error()
        data = get_channel_members_result_page_2.result.data
        assert len(data) == 5

    def test_remove_channel_members_endpoint_available(self):
        pn = _pubnub()
        remove_channel_members = pn.remove_channel_members()
        assert remove_channel_members is not None

    def test_remove_channel_members_is_endpoint(self):
        pn = _pubnub()
        remove_channel_members = pn.remove_channel_members()
        assert isinstance(remove_channel_members, RemoveChannelMembers)
        assert isinstance(remove_channel_members, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel_members/'
                         'remove_channel_members.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_remove_channel_members_happy_path(self):
        pn = _pubnub()

        some_uuid = "someuuid"
        some_uuid_with_custom = "someuuid_with_custom"

        remove_channel_members_result = pn.remove_channel_members()\
            .channel(TestObjectsV2ChannelMembers._some_channel_id)\
            .uuids([PNUUID.uuid(some_uuid)])\
            .include_custom(True)\
            .include_uuid(UUIDIncludeEndpoint.UUID_WITH_CUSTOM)\
            .sync()

        assert isinstance(remove_channel_members_result, Envelope)
        assert isinstance(remove_channel_members_result.result, PNRemoveChannelMembersResult)
        assert isinstance(remove_channel_members_result.status, PNStatus)
        assert not remove_channel_members_result.status.is_error()
        data = remove_channel_members_result.result.data
        assert isinstance(data, list)

        assert len([e for e in data if e['uuid']['id'] == some_uuid]) == 0
        assert len([e for e in data if e['uuid']['id'] == some_uuid_with_custom]) == 1

    def test_manage_channel_members_endpoint_available(self):
        pn = _pubnub()
        manage_channel_members = pn.manage_channel_members()
        assert manage_channel_members is not None

    def test_manage_channel_members_is_endpoint(self):
        pn = _pubnub()
        manage_channel_members = pn.manage_channel_members()
        assert isinstance(manage_channel_members, ManageChannelMembers)
        assert isinstance(manage_channel_members, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel_members/'
                         'manage_channel_members.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_manage_channel_members_happy_path(self):
        pn = _pubnub()

        some_uuid = "someuuid"
        some_uuid_with_custom = "someuuid_with_custom"

        manage_channel_members_result = pn.manage_channel_members()\
            .channel(TestObjectsV2ChannelMembers._some_channel_id)\
            .set([PNUUID.uuid(some_uuid)])\
            .remove([PNUUID.uuid(some_uuid_with_custom)])\
            .include_custom(True)\
            .include_uuid(UUIDIncludeEndpoint.UUID_WITH_CUSTOM)\
            .sync()

        assert isinstance(manage_channel_members_result, Envelope)
        assert isinstance(manage_channel_members_result.result, PNManageChannelMembersResult)
        assert isinstance(manage_channel_members_result.status, PNStatus)
        assert not manage_channel_members_result.status.is_error()
        data = manage_channel_members_result.result.data
        assert isinstance(data, list)

        assert len([e for e in data if e['uuid']['id'] == some_uuid]) == 1
        assert len([e for e in data if e['uuid']['id'] == some_uuid_with_custom]) == 0
