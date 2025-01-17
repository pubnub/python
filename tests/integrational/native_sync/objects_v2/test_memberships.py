from pubnub.endpoints.endpoint import Endpoint
from pubnub.endpoints.objects_v2.objects_endpoint import ChannelIncludeEndpoint
from pubnub.endpoints.objects_v2.memberships.get_memberships import GetMemberships
from pubnub.endpoints.objects_v2.memberships.manage_memberships import ManageMemberships
from pubnub.endpoints.objects_v2.memberships.remove_memberships import RemoveMemberships
from pubnub.endpoints.objects_v2.memberships.set_memberships import SetMemberships
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel_members import PNUUID
from pubnub.models.consumer.objects_v2.common import MemberIncludes
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership, PNSetMembershipsResult, \
    PNGetMembershipsResult, PNRemoveMembershipsResult, PNManageMembershipsResult
from pubnub.pubnub import PubNub
from pubnub.structures import Envelope
from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


def _pubnub():
    config = pnconf_env_copy()
    return PubNub(config)


class TestObjectsV2Memberships:
    _some_uuid = "someuuid"

    def test_set_memberships_endpoint_available(self):
        pn = _pubnub()
        set_memberships = pn.set_memberships()
        assert set_memberships is not None

    def test_set_memberships_is_endpoint(self):
        pn = _pubnub()
        set_memberships = pn.set_memberships()
        assert isinstance(set_memberships, SetMemberships)
        assert isinstance(set_memberships, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/memberships/set_memberships.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_set_memberships_happy_path(self):
        pn = _pubnub()

        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        pn.set_channel_metadata()\
            .channel(some_channel)\
            .set_name("some name")\
            .sync()

        custom_1 = {
            "key3": "val1",
            "key4": "val2"}
        pn.set_channel_metadata() \
            .channel(some_channel_with_custom) \
            .set_name("some name with custom") \
            .custom(custom_1) \
            .sync()

        custom_2 = {
            "key5": "val1",
            "key6": "val2"
        }

        channel_memberships_to_set = [
            PNChannelMembership.channel(some_channel),
            PNChannelMembership.channel_with_custom(some_channel_with_custom, custom_2)
        ]

        set_memberships_result = pn.set_memberships()\
            .uuid(TestObjectsV2Memberships._some_uuid)\
            .channel_memberships(channel_memberships_to_set)\
            .include_custom(True)\
            .include_channel(ChannelIncludeEndpoint.CHANNEL_WITH_CUSTOM)\
            .sync()

        assert isinstance(set_memberships_result, Envelope)
        assert isinstance(set_memberships_result.result, PNSetMembershipsResult)
        assert isinstance(set_memberships_result.status, PNStatus)
        assert not set_memberships_result.status.is_error()
        data = set_memberships_result.result.data
        assert isinstance(data, list)

        assert len([e for e in data if
                    e['channel']['id'] == some_channel or e['channel']['id'] == some_channel_with_custom]) == 2
        assert custom_1 in [e['channel'].get('custom', None) for e in data]
        assert len([e for e in data if e['custom'] == custom_2]) != 0

    def test_get_memberships_endpoint_available(self):
        pn = _pubnub()
        get_memberships = pn.get_memberships()
        assert get_memberships is not None

    def test_get_memberships_is_endpoint(self):
        pn = _pubnub()
        get_memberships = pn.get_memberships()
        assert isinstance(get_memberships, GetMemberships)
        assert isinstance(get_memberships, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/memberships/get_memberships.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_get_memberships_happy_path(self):
        pn = _pubnub()

        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        pn.set_channel_metadata() \
            .channel(some_channel) \
            .set_name("some name") \
            .sync()

        custom_1 = {
            "key3": "val1",
            "key4": "val2"}
        pn.set_channel_metadata() \
            .channel(some_channel_with_custom) \
            .set_name("some name with custom") \
            .custom(custom_1) \
            .sync()

        custom_2 = {
            "key5": "val1",
            "key6": "val2"
        }

        get_memberships_result = pn.get_memberships()\
            .uuid(TestObjectsV2Memberships._some_uuid)\
            .include_custom(True)\
            .include_channel(ChannelIncludeEndpoint.CHANNEL_WITH_CUSTOM)\
            .sync()

        assert isinstance(get_memberships_result, Envelope)
        assert isinstance(get_memberships_result.result, PNGetMembershipsResult)
        assert isinstance(get_memberships_result.status, PNStatus)
        assert not get_memberships_result.status.is_error()
        data = get_memberships_result.result.data
        assert isinstance(data, list)

        assert len([e for e in data if
                    e['channel']['id'] == some_channel or e['channel']['id'] == some_channel_with_custom]) == 2
        assert custom_1 in [e['channel'].get('custom', None) for e in data]
        assert len([e for e in data if e['custom'] == custom_2]) != 0

    def test_remove_memberships_endpoint_available(self):
        pn = _pubnub()
        remove_memberships = pn.remove_memberships()
        assert remove_memberships is not None

    def test_remove_memberships_is_endpoint(self):
        pn = _pubnub()
        remove_memberships = pn.remove_memberships()
        assert isinstance(remove_memberships, RemoveMemberships)
        assert isinstance(remove_memberships, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/memberships/remove_memberships.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_remove_memberships_happy_path(self):
        pn = _pubnub()

        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        remove_memberships_result = pn.remove_memberships()\
            .uuid(TestObjectsV2Memberships._some_uuid)\
            .channel_memberships([PNChannelMembership.channel(some_channel)])\
            .include_custom(True)\
            .include_channel(ChannelIncludeEndpoint.CHANNEL_WITH_CUSTOM)\
            .sync()

        assert isinstance(remove_memberships_result, Envelope)
        assert isinstance(remove_memberships_result.result, PNRemoveMembershipsResult)
        assert isinstance(remove_memberships_result.status, PNStatus)
        assert not remove_memberships_result.status.is_error()
        data = remove_memberships_result.result.data
        assert isinstance(data, list)

        assert len([e for e in data if e['channel']['id'] == some_channel]) == 0
        assert len([e for e in data if e['channel']['id'] == some_channel_with_custom]) == 1

    def test_manage_memberships_endpoint_available(self):
        pn = _pubnub()
        manage_memberships = pn.manage_memberships()
        assert manage_memberships is not None

    def test_manage_memberships_is_endpoint(self):
        pn = _pubnub()
        manage_memberships = pn.manage_memberships()
        assert isinstance(manage_memberships, ManageMemberships)
        assert isinstance(manage_memberships, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/memberships/manage_memberships.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_manage_memberships_happy_path(self):
        pn = _pubnub()

        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        manage_memberships_result = pn.manage_memberships() \
            .uuid(TestObjectsV2Memberships._some_uuid) \
            .set([PNChannelMembership.channel(some_channel)]) \
            .remove([PNChannelMembership.channel(some_channel_with_custom)]) \
            .include_custom(True) \
            .include_channel(ChannelIncludeEndpoint.CHANNEL_WITH_CUSTOM) \
            .sync()

        assert isinstance(manage_memberships_result, Envelope)
        assert isinstance(manage_memberships_result.result, PNManageMembershipsResult)
        assert isinstance(manage_memberships_result.status, PNStatus)
        assert not manage_memberships_result.status.is_error()
        data = manage_memberships_result.result.data
        assert isinstance(data, list)

        assert len([e for e in data if e['channel']['id'] == some_channel]) == 1
        assert len([e for e in data if e['channel']['id'] == some_channel_with_custom]) == 0

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/memberships/members_include_object.json',
                         filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
    def test_channel_members_with_include_object(self):
        config = pnconf_env_copy()
        pubnub = PubNub(config)

        some_channel = "somechannel"
        pubnub.set_uuid_metadata(uuid=self._some_uuid, name="Caroline", type='QA', status='online',
                                 custom={"removed": False}).sync()

        pubnub.set_channel_metadata(channel=some_channel, name="some name", description="This is a bit longer text",
                                    type="QAChannel", status="active", custom={"public": False}, ).sync()

        full_include = MemberIncludes(custom=True, status=True, type=True, total_count=True, user=True,
                                      user_custom=True, user_type=True, user_status=True)

        member = PNUUID.uuid_extended(self._some_uuid, type="QA", status="active",
                                      custom={"isCustom": True})

        set_response = pubnub.set_channel_members(channel=some_channel, uuids=[member], include=full_include).sync()

        self.assert_expected_response(set_response)

        get_response = pubnub.get_channel_members(channel=some_channel, include=full_include).sync()

        self.assert_expected_response(get_response)

        replacement = PNUUID.uuid(f'{self._some_uuid}_simple')

        manage_response = pubnub.manage_channel_members(channel=some_channel, uuids_to_set=[replacement],
                                                        uuids_to_remove=[member]).sync()

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