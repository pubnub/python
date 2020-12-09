from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, ListEndpoint, \
    IncludeCustomEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.channel import PNGetAllChannelMetadataResult


class GetAllChannels(ObjectsEndpoint, ListEndpoint, IncludeCustomEndpoint):
    GET_ALL_CHANNELS_PATH = "/v2/objects/%s/channels"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

    def build_path(self):
        return GetAllChannels.GET_ALL_CHANNELS_PATH % self.pubnub.config.subscribe_key

    def create_response(self, envelope):
        return PNGetAllChannelMetadataResult(envelope)

    def operation_type(self):
        return PNOperationType.PNGetAllChannelMetadataOperation

    def name(self):
        return "Get all Channels"

    def http_method(self):
        return HttpMethod.GET
