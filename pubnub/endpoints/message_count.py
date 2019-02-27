from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.message_count import PNMessageCountResult


class MessageCount(Endpoint):
    MESSAGE_COUNT_PATH = '/v3/history/sub-key/%s/message-counts/%s'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = []
        self._channels_timetoken = []

    def channel(self, channel):
        utils.extend_list(self._channel, channel)
        return self

    def channel_timetokens(self, timetokens):
        timetokens = [str(item) for item in timetokens]
        utils.extend_list(self._channels_timetoken, timetokens)
        return self

    def custom_params(self):
        params = {}
        if len(self._channels_timetoken) > 0:
            if len(self._channels_timetoken) > 1:
                params['channelsTimetoken'] = utils.join_items(self._channels_timetoken)
            else:
                params['timetoken'] = self._channels_timetoken[0]
        return params

    def build_path(self):
        return MessageCount.MESSAGE_COUNT_PATH % (
            self.pubnub.config.subscribe_key,
            utils.join_channels(self._channel)
        )

    def http_method(self):
        return HttpMethod.GET

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()

        if len(self._channels_timetoken) != len(self._channel):
            raise PubNubException('The number of channels and the number of timetokens do not match.')

    def create_response(self, result):  # pylint: disable=W0221
        return PNMessageCountResult(result)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNMessageCountOperation

    def name(self):
        return "Message Count"
