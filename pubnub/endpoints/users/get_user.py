import six

from pubnub.endpoints.endpoint import Endpoint
from pubnub.managers import TokenManagerProperties
from pubnub.models.consumer.user import PNGetUserResult
from pubnub.enums import HttpMethod, PNOperationType, PNResourceType
from pubnub.exceptions import PubNubException


class GetUser(Endpoint):
    GET_USER_PATH = '/v1/objects/%s/users/%s'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._user_id = None
        self._include = None

    def user_id(self, user_id):
        assert isinstance(user_id, six.string_types)
        self._user_id = user_id
        return self

    def include(self, data):
        self._include = data
        return self

    def custom_params(self):
        params = {}
        if self._include:
            params['include'] = self._include
        return params

    def build_path(self):
        if self._user_id is None:
            raise PubNubException('Provide user_id.')
        return GetUser.GET_USER_PATH % (self.pubnub.config.subscribe_key, self._user_id)

    def http_method(self):
        return HttpMethod.GET

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()

    def create_response(self, envelope):   # pylint: disable=W0221
        return PNGetUserResult(envelope)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNGetUserOperation

    def name(self):
        return 'Get user'

    def get_tms_properties(self):
        return TokenManagerProperties(
            resource_type=PNResourceType.USER,
            resource_id=self._user_id if self._user_id is not None else ""
        )
