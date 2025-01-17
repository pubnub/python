from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, UuidEndpoint, \
    IncludeCustomEndpoint, CustomAwareEndpoint, IncludeStatusTypeEndpoint, StatusTypeAwareEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.uuid import PNSetUUIDMetadataResult
from pubnub.structures import Envelope


class PNSetUUIDMetadataResultEnvelope(Envelope):
    result: PNSetUUIDMetadataResult
    status: PNStatus


class SetUuid(ObjectsEndpoint, UuidEndpoint, IncludeCustomEndpoint, CustomAwareEndpoint, IncludeStatusTypeEndpoint,
              StatusTypeAwareEndpoint):
    SET_UID_PATH = "/v2/objects/%s/uuids/%s"

    def __init__(self, pubnub, uuid: str = None, include_custom: bool = None, custom: dict = None,
                 include_status: bool = True, include_type: bool = True, status: str = None, type: str = None,
                 name: str = None, email: str = None, external_id: str = None, profile_url: str = None):
        ObjectsEndpoint.__init__(self, pubnub)
        UuidEndpoint.__init__(self, uuid=uuid)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        CustomAwareEndpoint.__init__(self, custom=custom)
        IncludeStatusTypeEndpoint.__init__(self, include_status=include_status, include_type=include_type)
        StatusTypeAwareEndpoint.__init__(self, status=status, type=type)

        self._name = name
        self._email = email
        self._external_id = external_id
        self._profile_url = profile_url

    def set_name(self, name: str):
        self._name = str(name)
        return self

    def email(self, email: str):
        self._email = str(email)
        return self

    def external_id(self, external_id: str):
        self._external_id = str(external_id)
        return self

    def profile_url(self, profile_url: str):
        self._profile_url = str(profile_url)
        return self

    def build_path(self):
        return SetUuid.SET_UID_PATH % (self.pubnub.config.subscribe_key, self._effective_uuid())

    def build_data(self):
        payload = {
            "name": self._name,
            "email": self._email,
            "externalId": self._external_id,
            "profileUrl": self._profile_url,
        }

        payload = CustomAwareEndpoint.build_data(self, payload)
        payload = StatusTypeAwareEndpoint.build_data(self, payload)
        return utils.write_value_as_string(payload)

    def validate_specific_params(self):
        self._validate_uuid()

    def create_response(self, envelope) -> PNSetUUIDMetadataResult:
        return PNSetUUIDMetadataResult(envelope)

    def sync(self) -> PNSetUUIDMetadataResultEnvelope:
        return PNSetUUIDMetadataResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNSetUuidMetadataOperation

    def name(self):
        return "Set UUID"

    def http_method(self):
        return HttpMethod.PATCH
