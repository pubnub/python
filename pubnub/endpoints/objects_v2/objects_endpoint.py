import logging
from abc import ABCMeta

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_UUID_MISSING, PNERR_CHANNEL_MISSING
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.objects_v2.page import Next, PNPage, Previous

logger = logging.getLogger("pubnub")


class ObjectsEndpoint(Endpoint):
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

        if isinstance(self, IncludeStatusTypeEndpoint):
            if self._include_status:
                inclusions.append("status")
            if self._include_type:
                inclusions.append("type")

        if isinstance(self, UUIDIncludeEndpoint):
            if self._uuid_details_level:
                if self._uuid_details_level == UUIDIncludeEndpoint.UUID:
                    inclusions.append("uuid")
                elif self._uuid_details_level == UUIDIncludeEndpoint.UUID_WITH_CUSTOM:
                    inclusions.append("uuid.custom")

        if isinstance(self, ChannelIncludeEndpoint):
            if self._channel_details_level:
                if self._channel_details_level == ChannelIncludeEndpoint.CHANNEL:
                    inclusions.append("channel")
                elif self._channel_details_level == ChannelIncludeEndpoint.CHANNEL_WITH_CUSTOM:
                    inclusions.append("channel.custom")

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

    def __init__(self, custom: dict = None):
        self._custom = None

    def custom(self, custom: dict):
        self._custom = dict(custom)
        self._include_custom = True
        return self


class StatusTypeAwareEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self, status: str = None, type: str = None):
        self._status = status
        self._type = type

    def set_status(self, status: str):
        self._status = status
        return self

    def set_type(self, type: str):
        self._type = type
        return self

    def build_data(self, payload):
        if self._status:
            payload["status"] = self._status
        if self._type:
            payload["type"] = self._type
        return payload


class ChannelEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self, channel: str = None):
        self._channel = channel

    def channel(self, channel: str):
        self._channel = str(channel)
        return self

    def _validate_channel(self):
        if self._channel is None or len(self._channel) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_MISSING)


class UuidEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self, uuid: str = None):
        self._uuid = uuid

    def uuid(self, uuid: str):
        self._uuid = str(uuid)
        return self

    def _effective_uuid(self):
        if self._uuid is not None:
            return self._uuid
        else:
            return self.pubnub.config.uuid

    def _validate_uuid(self):
        if self._effective_uuid() is None or len(self._effective_uuid()) == 0:
            raise PubNubException(pn_error=PNERR_UUID_MISSING)


class ListEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self, limit: int = None, filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                 page: PNPage = None):
        self._limit = limit
        self._filter = filter
        self._include_total_count = include_total_count
        self._sort_keys = sort_keys
        self._page = page

    def limit(self, limit: int):
        self._limit = int(limit)
        return self

    def filter(self, filter: str):
        self._filter = str(filter)
        return self

    def include_total_count(self, include_total_count: bool):
        self._include_total_count = bool(include_total_count)
        return self

    def sort(self, *sort_keys: list):
        self._sort_keys = sort_keys
        return self

    def page(self, page: PNPage):
        self._page = page
        return self


class IncludeCustomEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self, include_custom: bool = None):
        self._include_custom = include_custom

    def include_custom(self, include_custom: bool):
        self._include_custom = bool(include_custom)
        return self


class IncludeStatusTypeEndpoint:
    __metaclass__ = ABCMeta

    def __init__(self, include_status: bool = None, include_type: bool = None):
        self._include_status = include_status
        self._include_type = include_type

    def include_status(self, include_status: bool):
        self._include_status = bool(include_status)
        return self

    def include_type(self, include_type: bool):
        self._include_type = bool(include_type)
        return self


class UUIDIncludeEndpoint:
    __metaclass__ = ABCMeta

    UUID = 1
    UUID_WITH_CUSTOM = 2

    def __init__(self):
        self._uuid_details_level = None

    def include_uuid(self, uuid_details_level):
        self._uuid_details_level = uuid_details_level
        return self


class ChannelIncludeEndpoint:
    __metaclass__ = ABCMeta

    CHANNEL = 1
    CHANNEL_WITH_CUSTOM = 2

    def __init__(self):
        self._channel_details_level = None

    def include_channel(self, channel_details_level):
        self._channel_details_level = channel_details_level
        return self
