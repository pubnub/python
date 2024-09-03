from pubnub.enums import PNOperationType, HttpMethod
from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.v3.access_manager import PNRevokeTokenResult
from pubnub import utils
from pubnub.structures import Envelope


class PNRevokeTokenResultEnvelope(Envelope):
    result: PNRevokeTokenResult
    status: PNStatus


class RevokeToken(Endpoint):
    REVOKE_TOKEN_PATH = "/v3/pam/%s/grant/%s"

    def __init__(self, pubnub, token: str):
        Endpoint.__init__(self, pubnub)
        self.token = token

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_secret_key()

    def create_response(self, envelope):
        return PNRevokeTokenResult(envelope)

    def sync(self) -> PNRevokeTokenResultEnvelope:
        return PNRevokeTokenResultEnvelope(super().sync())

    def is_auth_required(self):
        return False

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def http_method(self):
        return HttpMethod.DELETE

    def custom_params(self):
        return {}

    def build_path(self):
        return RevokeToken.REVOKE_TOKEN_PATH % (self.pubnub.config.subscribe_key, utils.url_encode(self.token))

    def operation_type(self):
        return PNOperationType.PNAccessManagerRevokeToken

    def name(self):
        return "RevokeToken"
