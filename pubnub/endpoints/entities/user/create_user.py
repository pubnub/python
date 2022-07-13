from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, UserEndpoint, IncludeCustomEndpoint, \
    CustomAwareEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.entities.user import PNCreateUserResult
from pubnub.utils import write_value_as_string


class CreateUser(EntitiesEndpoint, UserEndpoint, IncludeCustomEndpoint, CustomAwareEndpoint):
    CREATE_USER_PATH = "/v2/objects/%s/uuids/%s"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        UserEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        CustomAwareEndpoint.__init__(self)

        self._name = None
        self._email = None
        self._external_id = None
        self._profile_url = None

    def user_status(self, user_status):
        self._status = user_status
        self._include_status = True
        return self

    def user_type(self, user_type):
        self._type = user_type
        self._include_type = True
        return self

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
        return CreateUser.CREATE_USER_PATH % (self.pubnub.config.subscribe_key, self._effective_user_id())

    def build_data(self):
        payload = {
            "name": self._name,
            "email": self._email,
            "externalId": self._external_id,
            "profileUrl": self._profile_url,
            "custom": self._custom
        }
        return write_value_as_string(payload)

    def validate_specific_params(self):
        self._validate_user_id()

    def create_response(self, envelope):
        return PNCreateUserResult(envelope)

    def operation_type(self):
        return PNOperationType.PNCreateUserOperation

    def name(self):
        return "Create User"

    def http_method(self):
        return HttpMethod.PATCH
