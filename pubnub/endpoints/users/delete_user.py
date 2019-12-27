import six

from pubnub.endpoints.endpoint import Endpoint
from pubnub.managers import TokenManagerProperties
from pubnub.models.consumer.user import PNDeleteUserResult
from pubnub.enums import HttpMethod, PNOperationType, PNResourceType
from pubnub.exceptions import PubNubException


class DeleteUser(Endpoint):
    DELETE_USER_PATH = '/v1/objects/%s/users/%s'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._user_id = None

    def user_id(self, user_id):
        assert isinstance(user_id, six.string_types)
        self._user_id = user_id
        return self

    def custom_params(self):
        return {}

    def build_data(self):
        return

    def build_path(self):
        if self._user_id is None:
            raise PubNubException('Provide user_id.')
        return DeleteUser.DELETE_USER_PATH % (self.pubnub.config.subscribe_key, self._user_id)

    def http_method(self):
        return HttpMethod.DELETE

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()

    def create_response(self, envelope):   # pylint: disable=W0221
        return PNDeleteUserResult(envelope)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNDeleteUserOperation

    def name(self):
        return 'Delete user'

    def get_tms_properties(self):
        return TokenManagerProperties(
            resource_type=PNResourceType.USER,
            resource_id=self._user_id if self._user_id is not None else ""
        )
