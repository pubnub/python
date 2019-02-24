from pubnub import utils
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.endpoints.endpoint import Endpoint


class HistoryDelete(Endpoint):  # pylint: disable=W0612
    HISTORY_DELETE_PATH = "/v3/history/sub-key/%s/channel/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = None
        self._start = None
        self._end = None

    def channel(self, channel):
        self._channel = channel
        return self

    def start(self, start):
        self._start = start
        return self

    def end(self, end):
        self._end = end
        return self

    def custom_params(self):
        params = {}

        if self._start is not None:
            params['start'] = str(self._start)

        if self._end is not None:
            params['end'] = str(self._end)

        return params

    def build_path(self):
        return HistoryDelete.HISTORY_DELETE_PATH % (
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel)
        )

    def http_method(self):
        return HttpMethod.DELETE

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()

    def create_response(self, endpoint):
        return {}

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNHistoryDeleteOperation

    def name(self):
        return "History delete"
