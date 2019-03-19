import six

from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_CHANNEL_MISSING, PNERR_PUSH_DEVICE_MISSING, PNERROR_PUSH_TYPE_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.push import PNPushRemoveChannelResult
from pubnub import utils


class RemoveChannelsFromPush(Endpoint):
    # v1/push/sub-key/{subKey}/devices/{pushToken}
    REMOVE_PATH = "/v1/push/sub-key/%s/devices/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channels = None
        self._device_id = None
        self._push_type = None

    def channels(self, channels):
        self._channels = channels
        return self

    def device_id(self, device_id):
        self._device_id = device_id
        return self

    def push_type(self, push_type):
        self._push_type = push_type
        return self

    def custom_params(self):
        params = {'remove': utils.join_items(self._channels), 'type': utils.push_type_to_string(self._push_type)}

        return params

    def build_path(self):
        return RemoveChannelsFromPush.REMOVE_PATH % (
            self.pubnub.config.subscribe_key, self._device_id)

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

        if not isinstance(self._channels, list) or len(self._channels) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_MISSING)

        if not isinstance(self._device_id, six.string_types) or len(self._device_id) == 0:
            raise PubNubException(pn_error=PNERR_PUSH_DEVICE_MISSING)

        if self._push_type is None:
            raise PubNubException(pn_error=PNERROR_PUSH_TYPE_MISSING)

    def create_response(self, envelope):
        return PNPushRemoveChannelResult()

    def is_auth_required(self):
        return True

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNRemovePushNotificationsFromChannelsOperation

    def name(self):
        return "RemoveChannelsFromPush"
