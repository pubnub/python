from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, ListEndpoint, \
    IncludeCustomEndpoint, IncludeStatusTypeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel import PNGetAllChannelMetadataResult
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.structures import Envelope


class PNGetAllChannelMetadataResultEnvelope(Envelope):
    result: PNGetAllChannelMetadataResult
    status: PNStatus


class GetAllChannels(ObjectsEndpoint, ListEndpoint, IncludeCustomEndpoint, IncludeStatusTypeEndpoint):
    GET_ALL_CHANNELS_PATH = "/v2/objects/%s/channels"

    def __init__(self, pubnub, include_custom=False, include_status=True, include_type=True, limit: int = None,
                 filter: str = None, include_total_count: bool = None, sort_keys: list = None, page: PNPage = None):
        ObjectsEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self, limit=limit, filter=filter, include_total_count=include_total_count,
                              sort_keys=sort_keys, page=page)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        IncludeStatusTypeEndpoint.__init__(self, include_status=include_status, include_type=include_type)

    def build_path(self):
        return GetAllChannels.GET_ALL_CHANNELS_PATH % self.pubnub.config.subscribe_key

    def create_response(self, envelope) -> PNGetAllChannelMetadataResult:
        return PNGetAllChannelMetadataResult(envelope)

    def sync(self) -> PNGetAllChannelMetadataResultEnvelope:
        return PNGetAllChannelMetadataResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNGetAllChannelMetadataOperation

    def name(self):
        return "Get all Channels"

    def http_method(self):
        return HttpMethod.GET
