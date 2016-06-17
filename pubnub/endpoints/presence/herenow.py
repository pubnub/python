from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.presence import PNHereNowResult, PNOccupantsData, PNHereNowChannelData


class HereNow(Endpoint):
    HERE_NOW_PATH = "/v2/presence/sub-key/%s/channel/%s"
    HERE_NOW_GLOBAL_PATH = "/v2/presence/sub-key/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channels = []
        self._channel_groups = []
        self._include_state = False
        self._include_uuids = True

    def channels(self, channels):
        utils.extend_list(self._channels, channels)
        return self

    def channel_groups(self, channel_groups):
        utils.extend_list(self._channel_groups, channel_groups)
        return self

    def include_state(self, should_include_state):
        self._include_state = should_include_state
        return self

    def include_uuids(self, include_uuids):
        self._include_uuids= include_uuids
        return self

    def build_params(self):
        params = self.default_params()

        if len(self._channel_groups) > 0:
            params['channel-groups'] = utils.join_items(self._channel_groups)

        if self._include_state:
            params['state'] = "1"

        if not self._include_uuids:
            params['disable_uuids'] = "1"

        return params

    def build_path(self):
        return HereNow.HERE_NOW_PATH % (self.pubnub.config.subscribe_key,
                                        utils.join_channels(self._channels))

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

    def create_response(self, envelope):
        if len(self._channels) > 1 or len(self._channel_groups) > 0:
            return self.parse_multiple_channel_response(envelope)
        else:
            return self.parse_single_channel_response(envelope)

    def parse_single_channel_response(self, envelope):
        return "qwer"

    def parse_multiple_channel_response(self, envelope):
        return PNHereNowResult.from_json(envelope['payload'])

    def operation_type(self):
        return PNOperationType.PNPublishOperation

    def name(self):
        return "HereNow"
