from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.time import PNTimeResponse
from pubnub.structures import Envelope


class PNTimeResponseEnvelope(Envelope):
    result: PNTimeResponse
    status: PNStatus


class Time(Endpoint):
    TIME_PATH = "/time/0"

    def custom_params(self):
        return {}

    def build_path(self):
        return Time.TIME_PATH

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        pass

    def is_auth_required(self):
        return False

    def create_response(self, envelope):
        return PNTimeResponse(envelope)

    def sync(self) -> PNTimeResponseEnvelope:
        return PNTimeResponseEnvelope(super().sync())

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNTimeOperation

    def name(self):
        return "Time"
