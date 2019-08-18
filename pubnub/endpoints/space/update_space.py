import six

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.space import PNUpdateSpaceResult
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.exceptions import PubNubException


class UpdateSpace(Endpoint):
    UPDATE_SPACE_PATH = '/v1/objects/%s/spaces/%s'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._space_id = None
        self._include = None
        self._data = None

    def space_id(self, space_id):
        assert isinstance(space_id, six.string_types)
        self._space_id = space_id
        return self

    def data(self, data):
        assert isinstance(data, dict)
        self._data = data
        return self

    def include(self, data):
        self._include = data
        return self

    def custom_params(self):
        params = {}
        if self._include:
            params['include'] = self._include
        return params

    def build_data(self):
        return utils.write_value_as_string(self._data)

    def build_path(self):
        if self._space_id is None:
            raise PubNubException('Provide space id.')
        return UpdateSpace.UPDATE_SPACE_PATH % (self.pubnub.config.subscribe_key, self._space_id)

    def http_method(self):
        return HttpMethod.PATCH

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        if self._data is None:
            raise PubNubException('No data supplied.')

    def create_response(self, envelope):   # pylint: disable=W0221
        return PNUpdateSpaceResult(envelope)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNUpdateSpaceOperation

    def name(self):
        return 'Update space'
