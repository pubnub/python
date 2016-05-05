from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.presence import PNHereNowResult, PNOccupantsData, PNHereNowChannelData


class HereNow(Endpoint):
    HERE_NOW_PATH = "/v2/presence/sub-key/%s/channel/%s"
    HERE_NOW_GLOBAL_PATH = "/v2/presence/sub-key/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channels = []
        self._channel_groups = []
        self._include_state = False

    def channels(self, channels):
        self._channels = channels
        return self

    def channel_groups(self, channel_groups):
        self._channel_groups = channel_groups
        return self

    def include_state(self, should_include_state):
        self._include_state = should_include_state
        return self

    def do_work(self):
        return self.pubnub.request(self.here_now_path(), self.build_params())

    def build_params(self):
        params = self.default_params()

        if len(self._channels) > 0:
            params['channels'] = ",".join(self._channels)

        params['state'] = "1"

        return params

    def here_now_path(self):
        if len(self._channels) > 0:
            channels = ','.join(self._channels)
        else:
            channels = ','

        return HereNow.HERE_NOW_PATH % (self.pubnub.config.subscribe_key, channels)

    def create_response(self, envelope):
        if len(self._channels) > 1 or len(self._channel_groups) > 0:
            return self.parse_multiple_channel_response(envelope)
        else:
            return self.parse_single_channel_response(envelope)

    def parse_single_channel_response(self, envelope):
        return "qwer"

    def parse_multiple_channel_response(self, envelope):

        json_env = envelope.json()
        payload = json_env['payload']
        raw_channels = payload['channels']
        channels = []

        for raw_channel, raw_data in raw_channels.items():
            occupants = []
            for uuid, state in raw_data.items():
                occupants.append(PNOccupantsData(uuid, state))

            channels.append(PNHereNowChannelData(
                channel_name=raw_channel,
                occupancy=int(raw_data['occupancy']),
                occupants=occupants
            ))

        res = PNHereNowResult(int(payload['total_channels']), int(payload['total_channels']), channels)

        return res

# Endpoint.register(HereNow)