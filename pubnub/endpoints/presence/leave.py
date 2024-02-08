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
        self._channels = []
        self._groups = []

    def channels(self, channels):
        if isinstance(channels, (list, tuple)):
            self._channels.extend(channels)
        else:
            self._channels.extend(utils.split_items(channels))

        return self

    def channel_groups(self, channel_groups):
        if isinstance(channel_groups, (list, tuple)):
            self._groups.extend(channel_groups)
        else:
            self._groups.extend(utils.split_items(channel_groups))

        return self

    def custom_params(self):
        params = {}

        if len(self._groups) > 0:
            params['channel-group'] = utils.join_items(self._groups)

        if hasattr(self.pubnub, '_subscription_manager'):
            params.update(self.pubnub._subscription_manager.get_custom_params())

        return params

    def build_path(self):
        return Leave.LEAVE_PATH % (self.pubnub.config.subscribe_key, utils.join_channels(self._channels))

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
        return self._channels

    def affected_channels_groups(self):
        return self._groups

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNUnsubscribeOperation

    def name(self):
        return "Leave"
