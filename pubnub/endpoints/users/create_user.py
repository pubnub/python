from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.managers import TokenManagerProperties
from pubnub.models.consumer.user import PNCreateUserResult
from pubnub.enums import HttpMethod, PNOperationType, PNResourceType
from pubnub.exceptions import PubNubException


class CreateUser(Endpoint):
    CREATE_USER_PATH = '/v1/objects/%s/users'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._include = None
        self._data = None

    def include(self, data):
        self._include = data
        return self

    def custom_params(self):
        params = {}
        if self._include:
            params['include'] = self._include
        return params

    def data(self, data):
        assert isinstance(data, dict)
        if 'id' not in data or 'name' not in data:
            raise PubNubException("User's id or name missing.")
        self._data = data
        return self

    def build_data(self):
        return utils.write_value_as_string(self._data)

    def validate_params(self):
        self.validate_subscribe_key()
        if self._data is None:
            raise PubNubException('No data supplied.')

    def build_path(self):
        return CreateUser.CREATE_USER_PATH % (self.pubnub.config.subscribe_key)

    def http_method(self):
        return HttpMethod.POST

    def is_auth_required(self):
        return True

    def create_response(self, envelope):  # pylint: disable=W0221
        return PNCreateUserResult(envelope)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNCreateUserOperation

    def name(self):
        return 'Create user'

    def get_tms_properties(self):
        return TokenManagerProperties(
            resource_type=PNResourceType.USER,
            resource_id=self._data['id'] if self._data is not None else ""
        )
