from typing import Optional, Union, List
from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.errors import PNERR_CHANNEL_OR_GROUP_MISSING
from pubnub.exceptions import PubNubException


class Subscribe(Endpoint):
    # /subscribe/<sub-key>/<channel>/<callback>/<timetoken>
    SUBSCRIBE_PATH = "/v2/subscribe/%s/%s/0"

    _channels: list = []
    _groups: list = []

    region: Optional[str] = None
    filter_expression: Optional[str] = None
    timetoken: Optional[str] = None
    with_presence: Optional[str] = None
    state: Optional[str] = None

    def __init__(self, pubnub, channels: Union[str, List[str]] = None,
                 groups: Union[str, List[str]] = None, region: Optional[str] = None,
                 filter_expression: Optional[str] = None, timetoken: Optional[str] = None,
                 with_presence: Optional[str] = None, state: Optional[str] = None):

        super(Subscribe, self).__init__(pubnub)
        self._channels = []
        if channels:
            utils.extend_list(self._channels, channels)
        self._groups = []
        if groups:
            utils.extend_list(self._groups, groups)

        self._region = region
        self._filter_expression = filter_expression
        self._timetoken = timetoken
        self._with_presence = with_presence
        self._state = state

    def channels(self, channels: Union[str, List[str]]) -> 'Subscribe':
        utils.extend_list(self._channels, channels)
        return self

    def channel_groups(self, groups: Union[str, List[str]]) -> 'Subscribe':
        utils.extend_list(self._groups, groups)
        return self

    def timetoken(self, timetoken) -> 'Subscribe':
        self._timetoken = timetoken
        return self

    def filter_expression(self, expr) -> 'Subscribe':
        self._filter_expression = expr
        return self

    def region(self, region) -> 'Subscribe':
        self._region = region
        return self

    def state(self, state) -> 'Subscribe':
        self._state = state
        return self

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

        if len(self._channels) == 0 and len(self._groups) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_OR_GROUP_MISSING)

    def build_path(self):
        channels = utils.join_channels(self._channels)
        return Subscribe.SUBSCRIBE_PATH % (self.pubnub.config.subscribe_key, channels)

    def custom_params(self):
        params = {}

        if len(self._groups) > 0:
            params['channel-group'] = utils.join_items_and_encode(self._groups)

        if self._filter_expression is not None and len(self._filter_expression) > 0:
            params['filter-expr'] = utils.url_encode(self._filter_expression)

        if self._timetoken is not None:
            params['tt'] = str(self._timetoken)

        if self._region is not None:
            params['tr'] = self._region

        if not self.pubnub.config.heartbeat_default_values:
            params['heartbeat'] = self.pubnub.config.presence_timeout

        if self._state is not None and len(self._state) > 0:
            params['state'] = utils.url_write(self._state)

        if hasattr(self.pubnub, '_subscription_manager'):
            params.update(self.pubnub._subscription_manager.get_custom_params())

        return params

    def create_response(self, envelope):
        return envelope

    def is_auth_required(self):
        return True

    def affected_channels(self):
        return self._channels

    def affected_channels_groups(self):
        return self._groups

    def request_timeout(self):
        return self.pubnub.config.subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNSubscribeOperation

    def name(self):
        return "Subscribe"
