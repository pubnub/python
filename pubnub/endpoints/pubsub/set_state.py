from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_CHANNEL_OR_GROUP_MISSING, PNERR_STATE_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.presence import PNSetStateResult


class SetState(Endpoint):
    # /v2/presence/sub-key/<subscribe_key>/channel/<channel>/uuid/<uuid>/data?state=<state>
    SET_STATE_PATH = "/v2/presence/sub-key/%s/channel/%s/uuid/%s/data"

    def __init__(self, pubnub, subscription_manager=None):
        Endpoint.__init__(self, pubnub)
        self._subscription_manager = subscription_manager
        self._channels = []
        self._groups = []
        self._state = None

    def channels(self, channels):
        utils.extend_list(self._channels, channels)
        return self

    def channel_groups(self, channel_groups):
        utils.extend_list(self._groups, channel_groups)
        return self

    def state(self, state):
        self._state = state
        return self

    def build_params(self):
        params = self.default_params()

        params['state'] = utils.write_value_as_string(self._state)

        if len(self._groups) > 0:
            params['channel-group'] = utils.join_items(self._groups)

        return params

    def build_path(self):
            return SetState.SET_STATE_PATH % (
                self.pubnub.config.subscribe_key,
                utils.join_channels(self._channels),
                self.pubnub.uuid
            )

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channels_and_groups()

        if self._state is None or not isinstance(self._state, dict):
            raise PubNubException(pn_error=PNERR_STATE_MISSING)

    def create_response(self, envelope):
        return PNSetStateResult(envelope['payload'])

    def affected_channels(self):
        return self._channels

    def affected_channels_groups(self):
        return self._groups

    def operation_type(self):
        return PNOperationType.PNSetStateOperation

    def name(self):
        return "SetState"
