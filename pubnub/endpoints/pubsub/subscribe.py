from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.errors import PNERR_CHANNEL_OR_GROUP_MISSING
from pubnub.exceptions import PubNubException


class Subscribe(Endpoint):
    # /subscribe/<sub-key>/<channel>/<callback>/<timetoken>
    SUBSCRIBE_PATH = "/v2/subscribe/%s/%s/0"

    def __init__(self, pubnub):
        super(Subscribe, self).__init__(pubnub)
        self._channels = []
        self._groups = []

        self._region = None
        self._filter_expression = None
        self._timetoken = None
        self._with_presence = None

    def channels(self, channels):
        if isinstance(channels, (list, tuple)):
            self._channels.extend(channels)
        else:
            self._channels.extend(utils.split_items(channels))

        return self

    def groups(self, groups):
        if isinstance(groups, (list, tuple)):
            self._groups.extend(groups)
        else:
            self._groups.extend(utils.split_items(groups))

        return self

    def timetoken(self, timetoken):
        self._timetoken = timetoken

        return self

    def filter_expression(self, expr):
        self._filter_expression = expr

        return self

    def region(self, region):
        self._region = region

        return self

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

        if len(self._channels) == 0 and len(self._groups) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_OR_GROUP_MISSING)

    def build_path(self):
        channels = "," if len(self._channels) is 0 else utils.join_items(self._channels)
        return Subscribe.SUBSCRIBE_PATH % (self.pubnub.config.subscribe_key, channels)

    def build_params(self):
        params = self.default_params()

        if len(self._groups) > 0:
            params['channel-group'] = utils.join_items(self._groups)

        if self._filter_expression is not None and len(self._filter_expression) > 0:
            params['filter-expr'] = self._filter_expression

        if self._timetoken is not None:
            params['tt'] = str(self._timetoken)

        if self._region is not None:
            params['tr'] = self._region

        return params

    def create_response(self, envelope):
        return envelope

    def affected_channels(self):
        return None

    def affected_channels_groups(self):
        return None

    def operation_type(self):
        return PNOperationType.PNSubscribeOperation

    def name(self):
        return "Subscribe"
