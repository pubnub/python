from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, IncludeCustomEndpoint, \
    ChannelEndpoint, CustomAwareEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.channel import PNSetChannelMetadataResult


class SetChannel(ObjectsEndpoint, ChannelEndpoint, IncludeCustomEndpoint, CustomAwareEndpoint):
    SET_CHANNEL_PATH = "/v2/objects/%s/channels/%s"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        ChannelEndpoint.__init__(self)
        CustomAwareEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

        self._name = None
        self._description = None

    def set_name(self, name):
        self._name = str(name)
        return self

    def description(self, description):
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
            "custom": self._custom
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope):
        return PNSetChannelMetadataResult(envelope)

    def operation_type(self):
        return PNOperationType.PNSetChannelMetadataOperation

    def name(self):
        return "Set UUID"

    def http_method(self):
        return HttpMethod.PATCH
