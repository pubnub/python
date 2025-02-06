import pytest
from pubnub.endpoints.endpoint import Endpoint
from pubnub.endpoints.objects_v2.channel.get_all_channels import GetAllChannels
from pubnub.endpoints.objects_v2.channel.get_channel import GetChannel
from pubnub.endpoints.objects_v2.channel.remove_channel import RemoveChannel
from pubnub.endpoints.objects_v2.channel.set_channel import SetChannel
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel import PNSetChannelMetadataResult, PNGetChannelMetadataResult, \
    PNRemoveChannelMetadataResult, PNGetAllChannelMetadataResult
from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
from pubnub.pubnub_asyncio import PubNubAsyncio
from pubnub.models.envelopes import AsyncioEnvelope
from tests.helper import pnconf_env_copy
from tests.integrational.vcr_helper import pn_vcr


def _pubnub():
    config = pnconf_env_copy()
    return PubNubAsyncio(config)


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

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/channel/set_channel.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_set_channel_happy_path(self):
        pn = _pubnub()

        set_channel_result = await pn.set_channel_metadata() \
            .include_custom(True) \
            .channel(TestObjectsV2Channel._some_channel_id) \
            .set_name(TestObjectsV2Channel._some_name) \
            .description(TestObjectsV2Channel._some_description) \
            .custom(TestObjectsV2Channel._some_custom) \
            .future()

        assert isinstance(set_channel_result, AsyncioEnvelope)
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

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/channel/get_channel.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_get_channel_happy_path(self):
        pn = _pubnub()

        get_channel_result = await pn.get_channel_metadata() \
            .include_custom(True) \
            .channel(TestObjectsV2Channel._some_channel_id) \
            .future()

        assert isinstance(get_channel_result, AsyncioEnvelope)
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

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/channel/remove_channel.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_remove_channel_happy_path(self):
        pn = _pubnub()

        remove_uid_result = await pn.remove_channel_metadata() \
            .channel(TestObjectsV2Channel._some_channel_id) \
            .future()

        assert isinstance(remove_uid_result, AsyncioEnvelope)
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

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/channel/get_all_channel.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_get_all_channel_happy_path(self):
        pn = _pubnub()

        await pn.set_channel_metadata() \
            .include_custom(True) \
            .channel(TestObjectsV2Channel._some_channel_id) \
            .set_name(TestObjectsV2Channel._some_name) \
            .description(TestObjectsV2Channel._some_description) \
            .custom(TestObjectsV2Channel._some_custom) \
            .future()

        get_all_channel_result = await pn.get_all_channel_metadata() \
            .include_custom(True) \
            .limit(10) \
            .include_total_count(True) \
            .sort(PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)) \
            .page(None) \
            .future()

        assert isinstance(get_all_channel_result, AsyncioEnvelope)
        assert isinstance(get_all_channel_result.result, PNGetAllChannelMetadataResult)
        assert isinstance(get_all_channel_result.status, PNStatus)
        assert not get_all_channel_result.status.is_error()
        data = get_all_channel_result.result.data
        assert isinstance(data, list)
        assert get_all_channel_result.result.total_count != 0
        assert get_all_channel_result.result.next is not None
        assert get_all_channel_result.result.prev is None

    @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/objects_v2/channel/if_matches_etag.json',
                         filter_query_parameters=['uuid', 'pnsdk', 'l_obj'], serializer='pn_json')
    @pytest.mark.asyncio
    async def test_if_matches_etag(self):
        pubnub = _pubnub()

        set_channel = await pubnub.set_channel_metadata(channel=self._some_channel_id, name=self._some_name).future()
        original_etag = set_channel.result.data.get('eTag')
        get_channel = await pubnub.get_channel_metadata(channel=self._some_channel_id).future()
        assert original_etag == get_channel.result.data.get('eTag')

        # Update without eTag should be possible
        set_channel = await pubnub.set_channel_metadata(channel=self._some_channel_id, name=f"{self._some_name}-2") \
            .future()

        # Response should contain new eTag
        new_etag = set_channel.result.data.get('eTag')
        assert original_etag != new_etag
        assert set_channel.result.data.get('name') == f"{self._some_name}-2"

        get_channel = await pubnub.get_channel_metadata(channel=self._some_channel_id).future()
        assert original_etag != get_channel.result.data.get('eTag')
        assert get_channel.result.data.get('name') == f"{self._some_name}-2"

        # Update with correct eTag should be possible
        set_channel = await pubnub.set_channel_metadata(channel=self._some_channel_id, name=f"{self._some_name}-3") \
            .if_matches_etag(new_etag) \
            .future()
        assert set_channel.result.data.get('name') == f"{self._some_name}-3"

        try:
            # Update with original - now outdated - eTag should fail
            set_channel = await pubnub.set_channel_metadata(
                channel=self._some_channel_id,
                name=f"{self._some_name}-3"
            ).if_matches_etag(original_etag).future()

        except PubNubException as e:
            assert e.get_status_code() == 412
            assert e.get_error_message().get('message') == 'Channel to update has been modified after it was read.'
