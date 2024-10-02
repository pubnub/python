from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, IncludeCustomEndpoint, ChannelEndpoint, \
    IncludeStatusTypeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel import PNGetChannelMetadataResult
from pubnub.structures import Envelope


class PNGetChannelMetadataResultEnvelope(Envelope):
    result: PNGetChannelMetadataResult
    status: PNStatus


class GetChannel(ObjectsEndpoint, ChannelEndpoint, IncludeCustomEndpoint, IncludeStatusTypeEndpoint):
    GET_CHANNEL_PATH = "/v2/objects/%s/channels/%s"

    def __init__(self, pubnub, channel: str = None, include_custom: bool = False, include_status: bool = True,
                 include_type: bool = True):
        ObjectsEndpoint.__init__(self, pubnub)
        ChannelEndpoint.__init__(self, channel=channel)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        IncludeStatusTypeEndpoint.__init__(self, include_status=include_status, include_type=include_type)

    def build_path(self):
        return GetChannel.GET_CHANNEL_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def validate_specific_params(self):
        self._validate_channel()

    def create_response(self, envelope) -> PNGetChannelMetadataResult:
        return PNGetChannelMetadataResult(envelope)

    def sync(self) -> PNGetChannelMetadataResultEnvelope:
        return PNGetChannelMetadataResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNGetChannelMetadataOperation

    def name(self):
        return "Get Channel"

    def http_method(self):
        return HttpMethod.GET
