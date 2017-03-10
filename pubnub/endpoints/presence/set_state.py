from pubnub import utils
from pubnub.dtos import StateOperation
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_STATE_MISSING, PNERR_STATE_SETTER_FOR_GROUPS_NOT_SUPPORTED_YET
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

    def custom_params(self):
        if self._subscription_manager is not None:
            self._subscription_manager.adapt_state_builder(StateOperation(
                channels=self._channels,
                channel_groups=self._groups,
                state=self._state
            ))

        params = {'state': utils.write_value_as_string(self._state)}

        if len(self._groups) > 0:
            params['channel-group'] = utils.join_items_and_encode(self._groups)

        return params

    def build_path(self):
            return SetState.SET_STATE_PATH % (
                self.pubnub.config.subscribe_key,
                utils.join_channels(self._channels),
                utils.url_encode(self.pubnub.uuid)
            )

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channels_and_groups()

        if len(self._channels) == 0 and len(self._groups) > 0:
            raise PubNubException(pn_error=PNERR_STATE_SETTER_FOR_GROUPS_NOT_SUPPORTED_YET)

        if self._state is None or not isinstance(self._state, dict):
            raise PubNubException(pn_error=PNERR_STATE_MISSING)

    def create_response(self, envelope):
        if 'status' in envelope and envelope['status'] is 200:
            return PNSetStateResult(envelope['payload'])
        else:
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
        return PNOperationType.PNSetStateOperation

    def name(self):
        return "SetState"
