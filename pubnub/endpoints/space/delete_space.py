import six

from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.space import PNDeleteSpaceResult
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.exceptions import PubNubException


class DeleteSpace(Endpoint):
    DELETE_DELETE_PATH = '/v1/objects/%s/spaces/%s'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._space_id = None

    def space_id(self, space_id):
        assert isinstance(space_id, six.string_types)
        self._space_id = space_id
        return self

    def custom_params(self):
        return {}

    def build_data(self):
        return

    def build_path(self):
        if self._space_id is None:
            raise PubNubException('Provide space id.')
        return DeleteSpace.DELETE_DELETE_PATH % (self.pubnub.config.subscribe_key, self._space_id)

    def http_method(self):
        return HttpMethod.DELETE

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()

    def create_response(self, envelope):   # pylint: disable=W0221
        return PNDeleteSpaceResult(envelope)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNDeleteSpaceOperation

    def name(self):
        return 'Delete space'
