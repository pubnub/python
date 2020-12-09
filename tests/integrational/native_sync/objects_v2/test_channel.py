from pubnub.endpoints.endpoint import Endpoint
from pubnub.endpoints.objects_v2.channel.get_all_channels import GetAllChannels
from pubnub.endpoints.objects_v2.channel.get_channel import GetChannel
from pubnub.endpoints.objects_v2.channel.remove_channel import RemoveChannel
from pubnub.endpoints.objects_v2.channel.set_channel import SetChannel
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel import PNSetChannelMetadataResult, PNGetChannelMetadataResult, \
    PNRemoveChannelMetadataResult, PNGetAllChannelMetadataResult
from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
from pubnub.pubnub import PubNub
from pubnub.structures import Envelope
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


def _pubnub():
    config = pnconf_copy()
    return PubNub(config)


class TestObjectsV2Channel:
    _some_channel_id = "somechannelid"
    _some_name = "Some name"
    _some_description = "Some description"
    _some_custom = {
        "key1": "val1",
        "key2": "val2"
    }

    def test_set_channel_endpoint_available(self):
        pn = _pubnub()
        set_channel = pn.set_channel_metadata()
        assert set_channel is not None
        assert isinstance(set_channel, SetChannel)
        assert isinstance(set_channel, Endpoint)

    def test_set_channel_is_endpoint(self):
        pn = _pubnub()
        set_channel = pn.set_channel_metadata()
        assert isinstance(set_channel, SetChannel)
        assert isinstance(set_channel, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel/set_channel.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_set_channel_happy_path(self):
        pn = _pubnub()

        set_channel_result = pn.set_channel_metadata() \
            .include_custom(True) \
            .channel(TestObjectsV2Channel._some_channel_id) \
            .set_name(TestObjectsV2Channel._some_name) \
            .description(TestObjectsV2Channel._some_description) \
            .custom(TestObjectsV2Channel._some_custom) \
            .sync()

        assert isinstance(set_channel_result, Envelope)
        assert isinstance(set_channel_result.result, PNSetChannelMetadataResult)
        assert isinstance(set_channel_result.status, PNStatus)
        assert not set_channel_result.status.is_error()
        data = set_channel_result.result.data
        assert data['id'] == TestObjectsV2Channel._some_channel_id
        assert data['name'] == TestObjectsV2Channel._some_name
        assert data['description'] == TestObjectsV2Channel._some_description
        assert data['custom'] == TestObjectsV2Channel._some_custom

    def test_get_channel_endpoint_available(self):
        pn = _pubnub()
        get_channel = pn.get_channel_metadata()
        assert get_channel is not None
        assert isinstance(get_channel, GetChannel)
        assert isinstance(get_channel, Endpoint)

    def test_get_channel_is_endpoint(self):
        pn = _pubnub()
        get_channel = pn.get_channel_metadata()
        assert isinstance(get_channel, GetChannel)
        assert isinstance(get_channel, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel/get_channel.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_get_channel_happy_path(self):
        pn = _pubnub()

        get_channel_result = pn.get_channel_metadata() \
            .include_custom(True) \
            .channel(TestObjectsV2Channel._some_channel_id) \
            .sync()

        assert isinstance(get_channel_result, Envelope)
        assert isinstance(get_channel_result.result, PNGetChannelMetadataResult)
        assert isinstance(get_channel_result.status, PNStatus)
        assert not get_channel_result.status.is_error()
        data = get_channel_result.result.data
        assert data['id'] == TestObjectsV2Channel._some_channel_id
        assert data['name'] == TestObjectsV2Channel._some_name
        assert data['description'] == TestObjectsV2Channel._some_description
        assert data['custom'] == TestObjectsV2Channel._some_custom

    def test_remove_channel_endpoint_available(self):
        pn = _pubnub()
        remove_channel = pn.remove_channel_metadata()
        assert remove_channel is not None
        assert isinstance(remove_channel, RemoveChannel)
        assert isinstance(remove_channel, Endpoint)

    def test_remove_channel_is_endpoint(self):
        pn = _pubnub()
        remove_channel = pn.remove_channel_metadata()
        assert isinstance(remove_channel, RemoveChannel)
        assert isinstance(remove_channel, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel/remove_channel.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_remove_channel_happy_path(self):
        pn = _pubnub()

        remove_uid_result = pn.remove_channel_metadata() \
            .channel(TestObjectsV2Channel._some_channel_id) \
            .sync()

        assert isinstance(remove_uid_result, Envelope)
        assert isinstance(remove_uid_result.result, PNRemoveChannelMetadataResult)
        assert isinstance(remove_uid_result.status, PNStatus)
        assert not remove_uid_result.status.is_error()

    def test_get_all_channel_endpoint_available(self):
        pn = _pubnub()
        get_all_channel = pn.get_all_channel_metadata()
        assert get_all_channel is not None
        assert isinstance(get_all_channel, GetAllChannels)
        assert isinstance(get_all_channel, Endpoint)

    def test_get_all_channel_is_endpoint(self):
        pn = _pubnub()
        get_all_channel = pn.get_all_channel_metadata()
        assert isinstance(get_all_channel, GetAllChannels)
        assert isinstance(get_all_channel, Endpoint)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/channel/get_all_channel.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_get_all_channel_happy_path(self):
        pn = _pubnub()

        pn.set_channel_metadata() \
            .include_custom(True) \
            .channel(TestObjectsV2Channel._some_channel_id) \
            .set_name(TestObjectsV2Channel._some_name) \
            .description(TestObjectsV2Channel._some_description) \
            .custom(TestObjectsV2Channel._some_custom) \
            .sync()

        get_all_channel_result = pn.get_all_channel_metadata() \
            .include_custom(True) \
            .limit(10) \
            .include_total_count(True) \
            .sort(PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)) \
            .page(None) \
            .sync()

        assert isinstance(get_all_channel_result, Envelope)
        assert isinstance(get_all_channel_result.result, PNGetAllChannelMetadataResult)
        assert isinstance(get_all_channel_result.status, PNStatus)
        assert not get_all_channel_result.status.is_error()
        data = get_all_channel_result.result.data
        assert isinstance(data, list)
        assert get_all_channel_result.result.total_count != 0
        assert get_all_channel_result.result.next is not None
        assert get_all_channel_result.result.prev is None
