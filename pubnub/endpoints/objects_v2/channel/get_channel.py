from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, IncludeCustomEndpoint, \
    ChannelEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.channel import PNGetChannelMetadataResult


class GetChannel(ObjectsEndpoint, ChannelEndpoint, IncludeCustomEndpoint):
    GET_CHANNEL_PATH = "/v2/objects/%s/channels/%s"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        ChannelEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

    def build_path(self):
        return GetChannel.GET_CHANNEL_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def validate_specific_params(self):
        self._validate_channel()

    def create_response(self, envelope):
        return PNGetChannelMetadataResult(envelope)

    def operation_type(self):
        return PNOperationType.PNGetChannelMetadataOperation

    def name(self):
        return "Get Channel"

    def http_method(self):
        return HttpMethod.GET
