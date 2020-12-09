from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, UuidEndpoint, \
    IncludeCustomEndpoint, CustomAwareEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.uuid import PNSetUUIDMetadataResult


class SetUuid(ObjectsEndpoint, UuidEndpoint, IncludeCustomEndpoint, CustomAwareEndpoint):
    SET_UID_PATH = "/v2/objects/%s/uuids/%s"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        UuidEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        CustomAwareEndpoint.__init__(self)

        self._name = None
        self._email = None
        self._external_id = None
        self._profile_url = None

    def set_name(self, name):
        self._name = str(name)
        return self

    def email(self, email):
        self._email = str(email)
        return self

    def external_id(self, external_id):
        self._external_id = str(external_id)
        return self

    def profile_url(self, profile_url):
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
            "custom": self._custom
        }
        return utils.write_value_as_string(payload)

    def validate_specific_params(self):
        self._validate_uuid()

    def create_response(self, envelope):
        return PNSetUUIDMetadataResult(envelope)

    def operation_type(self):
        return PNOperationType.PNSetUuidMetadataOperation

    def name(self):
        return "Set UUID"

    def http_method(self):
        return HttpMethod.PATCH
