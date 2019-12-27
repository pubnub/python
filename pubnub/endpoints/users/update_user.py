import six

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.managers import TokenManagerProperties
from pubnub.models.consumer.user import PNUpdateUserResult
from pubnub.enums import HttpMethod, PNOperationType, PNResourceType
from pubnub.exceptions import PubNubException


class UpdateUser(Endpoint):
    UPDATE_USER_PATH = '/v1/objects/%s/users/%s'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._user_id = None
        self._include = None
        self._data = None

    def user_id(self, user_id):
        assert isinstance(user_id, six.string_types)
        self._user_id = user_id
        return self

    def include(self, data):
        self._include = data
        return self

    def data(self, data):
        assert isinstance(data, dict)
        self._data = data
        return self

    def custom_params(self):
        params = {}
        if self._include:
            params['include'] = self._include
        return params

    def build_data(self):
        return utils.write_value_as_string(self._data)

    def build_path(self):
        if self._user_id is None:
            raise PubNubException('Provide user_id.')
        return UpdateUser.UPDATE_USER_PATH % (self.pubnub.config.subscribe_key, self._user_id)

    def http_method(self):
        return HttpMethod.PATCH

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        if self._data is None:
            raise PubNubException('No data supplied.')

    def create_response(self, envelope):   # pylint: disable=W0221
        return PNUpdateUserResult(envelope)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNUpdateUserOperation

    def name(self):
        return 'Update user'

    def get_tms_properties(self):
        return TokenManagerProperties(
            resource_type=PNResourceType.USER,
            resource_id=self._user_id if self._user_id is not None else ""
        )
