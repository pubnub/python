from typing import List, Union
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_CHANNEL_MISSING, PNERR_PUSH_DEVICE_MISSING, PNERROR_PUSH_TYPE_MISSING, \
    PNERR_PUSH_TOPIC_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType, PNPushType, PNPushEnvironment
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.push import PNPushRemoveChannelResult
from pubnub import utils
from pubnub.structures import Envelope


class PNPushRemoveChannelResultEnvelope(Envelope):
    result: PNPushRemoveChannelResult
    status: PNStatus


class RemoveChannelsFromPush(Endpoint):
    # v1/push/sub-key/{subKey}/devices/{pushToken}
    REMOVE_PATH = "/v1/push/sub-key/%s/devices/%s"
    # v2/push/sub-key/{subKey}/devices-apns2/{deviceApns2}
    REMOVE_PATH_APNS2 = "/v2/push/sub-key/%s/devices-apns2/%s"

    def __init__(self, pubnub, channels: Union[str, List[str]] = None, device_id: str = None,
                 push_type: PNPushType = None, topic: str = None, environment: PNPushEnvironment = None):
        Endpoint.__init__(self, pubnub)
        self._channels = []
        if channels:
            utils.extend_list(self._channels, channels)

        self._device_id = device_id
        self._push_type = push_type
        self._topic = topic
        self._environment = environment

    def channels(self, channels: Union[str, List[str]]) -> 'RemoveChannelsFromPush':
        utils.extend_list(self._channels, channels)
        return self

    def device_id(self, device_id: str) -> 'RemoveChannelsFromPush':
        self._device_id = device_id
        return self

    def push_type(self, push_type: PNPushType) -> 'RemoveChannelsFromPush':
        self._push_type = push_type
        return self

    def topic(self, topic: str) -> 'RemoveChannelsFromPush':
        self._topic = topic
        return self

    def environment(self, environment: PNPushEnvironment) -> 'RemoveChannelsFromPush':
        self._environment = environment
        return self

    def custom_params(self):
        params = {'remove': utils.join_items(self._channels)}

        if self._push_type != PNPushType.APNS2:
            params['type'] = utils.push_type_to_string(self._push_type)
        else:
            if self._environment is None:
                self._environment = PNPushEnvironment.DEVELOPMENT

            params['environment'] = self._environment
            params['topic'] = self._topic

        return params

    def build_path(self):
        if self._push_type != PNPushType.APNS2:
            return RemoveChannelsFromPush.REMOVE_PATH % (
                self.pubnub.config.subscribe_key, self._device_id)
        else:
            return RemoveChannelsFromPush.REMOVE_PATH_APNS2 % (
                self.pubnub.config.subscribe_key, self._device_id)

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

        if not isinstance(self._channels, list) or len(self._channels) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_MISSING)

        if not isinstance(self._device_id, str) or len(self._device_id) == 0:
            raise PubNubException(pn_error=PNERR_PUSH_DEVICE_MISSING)

        if self._push_type is None:
            raise PubNubException(pn_error=PNERROR_PUSH_TYPE_MISSING)

        if self._push_type == PNPushType.APNS2:
            if not isinstance(self._topic, str) or len(self._topic) == 0:
                raise PubNubException(pn_error=PNERR_PUSH_TOPIC_MISSING)

    def create_response(self, envelope) -> PNPushRemoveChannelResult:
        return PNPushRemoveChannelResult()

    def sync(self) -> PNPushRemoveChannelResultEnvelope:
        return PNPushRemoveChannelResultEnvelope(self.process_sync())

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
