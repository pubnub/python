from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.signal import PNSignalResult


class Signal(Endpoint):
    SIGNAL_PATH = '/v1/signal/%s/%s/%s'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = []
        self._message = None

    def channel(self, channel):
        utils.extend_list(self._channel, channel)
        return self

    def message(self, message):
        self._message = message
        return self

    def build_path(self):
        return Signal.SIGNAL_PATH % (
            self.pubnub.config.publish_key,
            self.pubnub.config.subscribe_key,
            utils.join_channels(self._channel)
        )

    def custom_params(self):
        return {}

    def build_data(self):
        cipher = self.pubnub.config.cipher_key
        msg = utils.write_value_as_string(self._message)
        if cipher is not None:
            return '"{}"'.format(self.pubnub.config.crypto.encrypt(cipher, msg))
        return msg

    def http_method(self):
        return HttpMethod.POST

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
