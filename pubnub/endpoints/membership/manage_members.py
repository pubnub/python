import six

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.membership import PNManageMembersResult
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.exceptions import PubNubException


class ManageMembers(Endpoint):
    MANAGE_MEMBERS_PATH = '/v1/objects/%s/spaces/%s/users'
    MAX_LIMIT = 100

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._start = None
        self._end = None
        self._limit = ManageMembers.MAX_LIMIT
        self._count = False
        self._include = None
        self._space_id = None
        self._data = None

    def space_id(self, space_id):
        assert isinstance(space_id, six.string_types)
        self._space_id = space_id
        return self

    def start(self, start):
        assert isinstance(start, six.string_types)
        self._start = start
        return self

    def end(self, end):
        assert isinstance(end, six.string_types)
        self._end = end
        return self

    def limit(self, limit):
        assert isinstance(limit, six.integer_types)
        self._limit = limit
        return self

    def count(self, count):
        self._count = bool(count)
        return self

    def include(self, data):
        self._include = data
        return self

    def data(self, data):
        assert isinstance(data, dict)
        self._data = data
        return self

    def build_data(self):
        if self._data is not None:
            return utils.write_value_as_string(self._data)

    def custom_params(self):
        params = {}

        if self._start is not None:
            params['start'] = self._start

        if self._end is not None and self._start is None:
            params['end'] = self._end

        if self._count is True:
            params['count'] = True

        if self._limit != ManageMembers.MAX_LIMIT:
            params['limit'] = self._limit

        if self._include:
            params['include'] = utils.join_items(self._include)

        return params

    def build_path(self):
        if self._space_id is None:
            raise PubNubException('Provide space_id.')
        return ManageMembers.MANAGE_MEMBERS_PATH % (self.pubnub.config.subscribe_key, self._space_id)

    def http_method(self):
        return HttpMethod.PATCH

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        if self._space_id is None:
            raise PubNubException('Provide space_id.')

    def create_response(self, envelope):   # pylint: disable=W0221
        return PNManageMembersResult(envelope)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNManageMembersOperation

    def name(self):
        return 'Update members'
