import six

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.history import PNHistoryResult


class History(Endpoint):
    HISTORY_PATH = "/v2/history/sub-key/%s/channel/%s"
    MAX_COUNT = 100

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = None
        self._start = None
        self._end = None
        self._reverse = None
        self._count = None
        self._include_timetoken = None

    def channel(self, channel):
        self._channel = channel
        return self

    def start(self, start):
        assert isinstance(start, six.integer_types)
        self._start = start
        return self

    def end(self, end):
        assert isinstance(end, six.integer_types)
        self._end = end
        return self

    def reverse(self, reverse):
        assert isinstance(reverse, bool)
        self._reverse = reverse
        return self

    def count(self, count):
        assert isinstance(count, six.integer_types)
        self._count = count
        return self

    def include_timetoken(self, include_timetoken):
        assert isinstance(include_timetoken, bool)
        self._include_timetoken = include_timetoken
        return self

    def custom_params(self):
        params = {}

        if self._start is not None:
            params['start'] = str(self._start)

        if self._end is not None:
            params['end'] = str(self._end)

        if self._count is not None and 0 < self._count <= History.MAX_COUNT:
            params['count'] = str(self._count)
        else:
            params['count'] = '100'

        if self._reverse is not None:
            params['reverse'] = "true" if self._reverse else "false"

        if self._include_timetoken is not None:
            params['include_token'] = "true" if self._include_timetoken else "false"

        return params

    def build_path(self):
            return History.HISTORY_PATH % (
                self.pubnub.config.subscribe_key,
                utils.url_encode(self._channel)
            )

    def http_method(self):
        return HttpMethod.GET

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()

    def create_response(self, envelope):
        return PNHistoryResult.from_json(
            json_input=envelope,
            crypto=self.pubnub.config.crypto,
            include_tt_option=self._include_timetoken,
            cipher=self.pubnub.config.cipher_key)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNHistoryOperation

    def name(self):
        return "History"
