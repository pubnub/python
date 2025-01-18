from pubnub.endpoints.endpoint import Endpoint
from pubnub.endpoints.objects_v2.objects_endpoint import UUIDIncludeEndpoint
from pubnub.endpoints.objects_v2.members.get_channel_members import GetChannelMembers
from pubnub.endpoints.objects_v2.members.manage_channel_members import ManageChannelMembers
from pubnub.endpoints.objects_v2.members.remove_channel_members import RemoveChannelMembers
from pubnub.endpoints.objects_v2.members.set_channel_members import SetChannelMembers
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel_members import PNUUID, JustUUID, PNGetChannelMembersResult, \
    PNSetChannelMembersResult, PNRemoveChannelMembersResult, PNManageChannelMembersResult, PNUserMember
from pubnub.models.consumer.objects_v2.common import MemberIncludes
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.pubnub import PubNub
from pubnub.structures import Envelope
from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


def _pubnub():
    config = pnconf_env_copy()
    return PubNub(config)


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel_members/setup_module.json',
                     filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
def setup_module():
    pubnub = _pubnub()
    pubnub.remove_uuid_metadata("someuuid").sync()
    pubnub.remove_uuid_metadata("otheruuid").sync()
    pubnub.remove_channel_metadata("somechannelid").sync()
    pubnub.remove_channel_members("somechannelid", [
        PNUserMember("someuuid"),
        PNUserMember("otheruuid"),
        PNUserMember('someuuid_simple')
    ]).sync()


class TestObjectsV2ChannelMembers:
    _some_channel_id = "somechannelid"
    _some_uuid = 'someuuid'
    _other_uuid = 'otheruuid'

    def test_set_channel_members_endpoint_available(self):
        pn = _pubnub()
        set_channel_members = pn.set_channel_members()
        assert set_channel_members is not None

    def test_set_channel_members_is_endpoint(self):
        pn = _pubnub()
        set_channel_members = pn.set_channel_members()
        assert isinstance(set_channel_members, SetChannelMembers)
        assert isinstance(set_channel_members, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel_members/set_channel_members.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
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

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel_members/get_channel_members.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
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
        'tests/integrational/fixtures/native_sync/objects_v2/channel_members/get_channel_members_with_pagination.json',
        filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
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
                         'remove_channel_members.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
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
                         'manage_channel_members.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
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

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel_members/'
                         'channel_members_with_include_object.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_channel_members_with_include_object(self):
        config = pnconf_env_copy()
        pubnub = PubNub(config)

        some_channel = "somechannel"
        pubnub.set_uuid_metadata(
            uuid=self._some_uuid,
            name="Caroline",
            type='QA',
            status='online',
            custom={"removed": False}
        ).sync()

        pubnub.set_channel_metadata(
            channel=some_channel,
            name="some name",
            description="This is a bit longer text",
            type="QAChannel",
            status="active",
            custom={"public": False}
        ).sync()

        full_include = MemberIncludes(
            custom=True,
            status=True,
            type=True,
            total_count=True,
            user=True,
            user_custom=True,
            user_type=True,
            user_status=True
        )

        member = PNUserMember(
            self._some_uuid,
            status="active",
            type="QA",
            custom={"isCustom": True}
        )

        set_response = pubnub.set_channel_members(
            channel=some_channel,
            uuids=[member],
            include=full_include
        ).sync()

        self.assert_expected_response(set_response)

        get_response = pubnub.get_channel_members(channel=some_channel, include=full_include).sync()

        self.assert_expected_response(get_response)

        # the old way to add a simple uuid
        replacement = PNUUID.uuid(self._other_uuid)

        manage_response = pubnub.manage_channel_members(
            channel=some_channel,
            uuids_to_set=[replacement],
            uuids_to_remove=[member]
        ).sync()

        assert manage_response.status.is_error() is False
        assert len(manage_response.result.data) == 1
        assert manage_response.result.data[0]['uuid']['id'] == replacement._uuid

        rem_response = pubnub.remove_channel_members(channel=some_channel, uuids=[replacement]).sync()

        assert rem_response.status.is_error() is False

        get_response = pubnub.get_channel_members(channel=some_channel, include=full_include).sync()

        assert get_response.status.is_error() is False
        assert get_response.result.data == []

    def assert_expected_response(self, response):
        assert response is not None
        assert response.status.is_error() is False
        result = response.result.data
        assert result is not None
        assert len(result) == 1
        member_data = result[0]
        assert member_data['status'] == 'active'
        assert member_data['type'] == 'QA'
        user_data = result[0]['uuid']
        assert user_data['id'] == self._some_uuid
        assert user_data['name'] == 'Caroline'
        assert user_data['externalId'] is None
        assert user_data['profileUrl'] is None
        assert user_data['email'] is None
        assert user_data['type'] == 'QA'
        assert user_data['status'] == 'online'
        assert user_data['custom'] == {'removed': False}
