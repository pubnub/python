from typing import List, Union
from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.presence import PNGetStateResult
from pubnub.endpoints.mixins import UUIDValidatorMixin
from pubnub.structures import Envelope


class PNGetStateResultEnvelope(Envelope):
    result: PNGetStateResult
    status: PNStatus


class GetState(Endpoint, UUIDValidatorMixin):
    # /v2/presence/sub-key/<subscribe_key>/channel/<channel>/uuid/<uuid>/data?state=<state>
    GET_STATE_PATH = "/v2/presence/sub-key/%s/channel/%s/uuid/%s"

    def __init__(self, pubnub, channels: Union[str, List[str]] = None, channel_groups: Union[str, List[str]] = None,
                 uuid: str = None):
        Endpoint.__init__(self, pubnub)
        self._channels = []
        if channels:
            utils.extend_list(self._channels, channels)

        self._groups = []
        if channel_groups:
            utils.extend_list(self._groups, channel_groups)

        self._uuid = self.pubnub.uuid
        if uuid:
            self._uuid = uuid

    def channels(self, channels: Union[str, List[str]]) -> 'GetState':
        utils.extend_list(self._channels, channels)
        return self

    def uuid(self, uuid: str) -> 'GetState':
        self._uuid = uuid
        return self

    def channel_groups(self, channel_groups: Union[str, List[str]]) -> 'GetState':
        utils.extend_list(self._groups, channel_groups)
        return self

    def custom_params(self):
        params = {}

        if len(self._groups) > 0:
            params['channel-group'] = utils.join_items(self._groups)

        return params

    def build_path(self):
        return GetState.GET_STATE_PATH % (
            self.pubnub.config.subscribe_key,
            utils.join_channels(self._channels),
            utils.url_encode(self._uuid)
        )

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channels_and_groups()
        self.validate_uuid()

    def create_response(self, envelope) -> PNGetStateResult:
        if len(self._channels) == 1 and len(self._groups) == 0:
            channels = {self._channels[0]: envelope['payload']}
        else:
            channels = envelope['payload']['channels']

        return PNGetStateResult(channels)

    def sync(self) -> PNGetStateResultEnvelope:
        return PNGetStateResultEnvelope(super().sync())

    def is_auth_required(self):
        return True

    def affected_channels(self):
        return self._channels

    def affected_channels_groups(self):
        return self._groups

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNGetState

    def name(self):
        return "GetState"
