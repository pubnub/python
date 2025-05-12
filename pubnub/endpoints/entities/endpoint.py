import logging
from abc import ABCMeta

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_SPACE_MISSING, PNERR_USER_ID_MISSING
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.entities.page import Next, Previous

logger = logging.getLogger("pubnub")


class EntitiesEndpoint(Endpoint):
    __metaclass__ = ABCMeta

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)

    def is_auth_required(self):
        return True

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_specific_params()

    def validate_specific_params(self):
        pass

    def encoded_params(self):
        params = {}
        if isinstance(self, ListEndpoint):
            if self._filter:
                params["filter"] = utils.url_encode(str(self._filter))
        return params

    def custom_params(self):
        params = {}
        inclusions = []

        if isinstance(self, IncludeCustomEndpoint):
            if self._include_custom:
                inclusions.append("custom")

        if isinstance(self, UserIDIncludeEndpoint):
            if self._uuid_details_level:
                if self._uuid_details_level == UserIDIncludeEndpoint.USER_ID:
                    inclusions.append("user_id")
                elif self._uuid_details_level == UserIDIncludeEndpoint.USER_ID_WITH_CUSTOM:
                    inclusions.append("user_id.custom")

        if isinstance(self, SpaceIDIncludeEndpoint):
            if self._space_details_level:
                if self._space_details_level == SpaceIDIncludeEndpoint.CHANNEL:
                    inclusions.append("space")
                elif self._space_details_level == SpaceIDIncludeEndpoint.CHANNEL_WITH_CUSTOM:
                    inclusions.append("space.custom")

        if isinstance(self, ListEndpoint):
            if self._filter:
                params["filter"] = str(self._filter)

            if self._limit:
                params["limit"] = int(self._limit)

            if self._include_total_count:
                params["count"] = bool(self._include_total_count)

            if self._sort_keys:
                joined_sort_params_array = []
                for sort_key in self._sort_keys:
                    joined_sort_params_array.append("%s:%s" % (sort_key.key_str(), sort_key.dir_str()))

                params["sort"] = ",".join(joined_sort_params_array)

            if self._page:
                if isinstance(self._page, Next):
                    params["start"] = self._page.hash
                elif isinstance(self._page, Previous):
                    params["end"] = self._page.hash
                else:
                    raise ValueError()

        if len(inclusions) > 0:
            params["include"] = ",".join(inclusions)

        return params


class CustomAwareEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self):
        self._custom = None

    def custom(self, custom):
        self._custom = dict(custom)
        return self


class SpaceEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self):
        self._space_id = None

    def space_id(self, space):
        self._space_id = str(space)
        return self

    def _validate_space_id(self):
        if self._space_id is None or len(self._space_id) == 0:
            raise PubNubException(pn_error=PNERR_SPACE_MISSING)


class UserEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self):
        self._user_id = None

    def user_id(self, user_id):
        self._user_id = str(user_id)
        return self

    def _effective_user_id(self):
        if self._user_id is not None:
            return self._user_id
        else:
            return self.pubnub.config.user_id

    def _validate_user_id(self):
        if self._effective_user_id() is None or len(self._effective_user_id()) == 0:
            raise PubNubException(pn_error=PNERR_USER_ID_MISSING)


class UsersEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self):
        self._users = None

    def users(self, users):
        self._users = users
        return self


class SpacesEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self):
        self._spaces = None

    def spaces(self, spaces):
        self._spaces = spaces
        return self


class ListEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self, limit: int = None, filter: str = None, include_total_count: bool = None,
                 sort_keys: list = None, page: str = None):
        self._limit = limit
        self._filter = filter
        self._include_total_count = include_total_count
        self._sort_keys = sort_keys
        self._page = page

    def limit(self, limit):
        self._limit = int(limit)
        return self

    def filter(self, filter):
        self._filter = str(filter)
        return self

    def include_total_count(self, include_total_count):
        self._include_total_count = bool(include_total_count)
        return self

    def sort(self, *sort_keys):
        self._sort_keys = sort_keys
        return self

    def page(self, page):
        self._page = page
        return self


class IncludeCustomEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self):
        self._include_custom = None

    def include_custom(self, include_custom):
        self._include_custom = bool(include_custom)
        return self


class UserIDIncludeEndpoint:
    __metaclass__ = ABCMeta

    USER_ID = 1
    USER_ID_WITH_CUSTOM = 2

    def __init__(self):
        self._user_id_details_level = None

    def include_user_id(self, user_id_details_level):
        self._user_id_details_level = user_id_details_level
        return self


class SpaceIDIncludeEndpoint:
    __metaclass__ = ABCMeta

    SPACE = 1
    SPACE_WITH_CUSTOM = 2

    def __init__(self):
        self._space_details_level = None

    def include_space(self, space_details_level):
        self._space_details_level = space_details_level
        return self
