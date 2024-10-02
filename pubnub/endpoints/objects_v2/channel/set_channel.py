from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, IncludeCustomEndpoint, \
    ChannelEndpoint, CustomAwareEndpoint, IncludeStatusTypeEndpoint, StatusTypeAwareEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel import PNSetChannelMetadataResult
from pubnub.structures import Envelope


class PNSetChannelMetadataResultEnvelope(Envelope):
    result: PNSetChannelMetadataResult
    status: PNStatus


class SetChannel(ObjectsEndpoint, ChannelEndpoint, IncludeCustomEndpoint, CustomAwareEndpoint,
                 IncludeStatusTypeEndpoint, StatusTypeAwareEndpoint):
    SET_CHANNEL_PATH = "/v2/objects/%s/channels/%s"

    def __init__(self, pubnub, channel: str = None, custom: dict = None, include_custom: bool = False,
                 include_status: bool = True, include_type: bool = True, name: str = None, description: str = None,
                 status: str = None, type: str = None):
        ObjectsEndpoint.__init__(self, pubnub)
        ChannelEndpoint.__init__(self, channel=channel)
        CustomAwareEndpoint.__init__(self, custom=custom)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        IncludeStatusTypeEndpoint.__init__(self, include_status=include_status, include_type=include_type)
        self._name = name
        self._description = description
        self._status = status
        self._type = type

    def set_name(self, name: str) -> 'SetChannel':
        self._name = str(name)
        return self

    def set_status(self, status: str = None) -> 'SetChannel':
        self._status = status
        return self

    def set_type(self, type: str = None) -> 'SetChannel':
        self._type = type
        return self

    def description(self, description) -> 'SetChannel':
        self._description = str(description)
        return self

    def validate_specific_params(self):
        self._validate_channel()

    def build_path(self):
        return SetChannel.SET_CHANNEL_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def build_data(self):
        payload = {
            "name": self._name,
            "description": self._description,
            "status": self._status,
            "type": self._type,
            "custom": self._custom
        }
        payload = StatusTypeAwareEndpoint.build_data(self, payload)
        return utils.write_value_as_string(payload)

    def create_response(self, envelope) -> PNSetChannelMetadataResult:
        return PNSetChannelMetadataResult(envelope)

    def sync(self) -> PNSetChannelMetadataResultEnvelope:
        return PNSetChannelMetadataResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNSetChannelMetadataOperation

    def name(self):
        return "Set UUID"

    def http_method(self):
        return HttpMethod.PATCH
