from typing import Optional
from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.presence import PNWhereNowResult
from pubnub.endpoints.mixins import UUIDValidatorMixin
from pubnub.structures import Envelope


class PNWhereNowResultEnvelope(Envelope):
    result: PNWhereNowResult
    status: PNStatus


class WhereNow(Endpoint, UUIDValidatorMixin):
    # /v2/presence/sub-key/<subscribe_key>/uuid/<uuid>
    WHERE_NOW_PATH = "/v2/presence/sub-key/%s/uuid/%s"

    def __init__(self, pubnub, uuid: Optional[str] = None):
        Endpoint.__init__(self, pubnub)
        self._uuid = pubnub.config.uuid
        if uuid:
            self._uuid = uuid

    def uuid(self, uuid: str) -> 'WhereNow':
        self._uuid = uuid
        return self

    def custom_params(self):
        return {}

    def build_path(self):
        return WhereNow.WHERE_NOW_PATH % (self.pubnub.config.subscribe_key, utils.url_encode(self._uuid))

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_uuid()

    def is_auth_required(self):
        return True

    def create_response(self, envelope):
        return PNWhereNowResult.from_json(envelope)

    def sync(self) -> PNWhereNowResultEnvelope:
        return PNWhereNowResultEnvelope(super().sync())

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNWhereNowOperation

    def name(self):
        return "WhereNow"
