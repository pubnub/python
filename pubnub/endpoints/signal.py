from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.signal import PNSignalResult


class Signal(Endpoint):
    SIGNAL_PATH = '/signal/%s/%s/0/%s/0/%s'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = None
        self._message = None
        self._space_id = None
        self._message_type = None

    def channel(self, channel):
        self._channel = str(channel)
        return self

    def message(self, message):
        self._message = message
        return self

    def space_id(self, space_id: str):
        self._space_id = str(space_id)
        return self

    def message_type(self, message_type: str):
        self._message_type = message_type
        return self

    def build_path(self):
        stringified_message = utils.write_value_as_string(self._message)
        msg = utils.url_encode(stringified_message)
        return Signal.SIGNAL_PATH % (
            self.pubnub.config.publish_key, self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel), msg
        )

    def custom_params(self):
        params = {}

        if self._message_type is not None:
            params['type'] = self._message_type

        if self._space_id is not None:
            params['space-id'] = self._space_id

        return params

    def http_method(self):
        return HttpMethod.GET

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_publish_key()
        self.validate_channel()

    def create_response(self, result):  # pylint: disable=W0221
        return PNSignalResult(result)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNSignalOperation

    def name(self):
        return "Signal"
