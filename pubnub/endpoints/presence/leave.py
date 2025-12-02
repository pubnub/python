from typing import Set, Union, List

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_CHANNEL_OR_GROUP_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType


class Leave(Endpoint):
    # /v2/presence/sub-key/<subscribe_key>/channel/<channel>/leave?uuid=<uuid>
    LEAVE_PATH = "/v2/presence/sub-key/%s/channel/%s/leave"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channels: Set[str] = set()
        self._groups: Set[str] = set()

    def channels(self, channels: Union[str, List[str]]) -> 'Leave':
        utils.update_set(self._channels, channels)
        return self

    def channel_groups(self, channel_groups: Union[str, List[str]]) -> 'Leave':
        utils.update_set(self._groups, channel_groups)
        return self

    def custom_params(self):
        params = {}

        if len(self._groups) > 0:
            params['channel-group'] = utils.join_items(self._groups, True)

        if hasattr(self.pubnub, '_subscription_manager'):
            params.update(self.pubnub._subscription_manager.get_custom_params())

        return params

    def build_path(self):
        return Leave.LEAVE_PATH % (self.pubnub.config.subscribe_key, utils.join_channels(self._channels, True))

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

        if len(self._channels) == 0 and len(self._groups) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_OR_GROUP_MISSING)

    def create_response(self, envelope):
        return envelope

    def is_auth_required(self):
        return True

    def affected_channels(self):
        return sorted(self._channels)

    def affected_channels_groups(self):
        return sorted(self._groups)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNUnsubscribeOperation

    def name(self):
        return "Leave"
