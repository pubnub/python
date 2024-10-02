from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, ChannelEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel import PNRemoveChannelMetadataResult
from pubnub.structures import Envelope


class PNRemoveChannelMetadataResultEnvelope(Envelope):
    result: PNRemoveChannelMetadataResult
    status: PNStatus


class RemoveChannel(ObjectsEndpoint, ChannelEndpoint):
    REMOVE_CHANNEL_PATH = "/v2/objects/%s/channels/%s"

    def __init__(self, pubnub, channel: str = None):
        ObjectsEndpoint.__init__(self, pubnub)
        ChannelEndpoint.__init__(self, channel=channel)

    def build_path(self):
        return RemoveChannel.REMOVE_CHANNEL_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def validate_specific_params(self):
        self._validate_channel()

    def create_response(self, envelope) -> PNRemoveChannelMetadataResult:
        return PNRemoveChannelMetadataResult(envelope)

    def sync(self) -> PNRemoveChannelMetadataResultEnvelope:
        return PNRemoveChannelMetadataResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNRemoveChannelMetadataOperation

    def name(self):
        return "Remove Channel"

    def http_method(self):
        return HttpMethod.DELETE
