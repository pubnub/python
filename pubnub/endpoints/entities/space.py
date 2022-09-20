from pubnub.endpoints.entities.endpoint import EntitiesEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.errors import PNERR_SPACE_MISSING
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.entities.page import Next, Previous
from pubnub.models.consumer.entities.space import PNCreateSpaceResult, PNRemoveSpaceResult, PNUpdateSpaceResult, \
    PNUpsertSpaceResult, PNFetchSpaceResult, PNFetchSpacesResult
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.utils import write_value_as_string


class EntitiesSpaceEndpoint(EntitiesEndpoint):
    SPACE_PATH = "/v3/objects/%s/spaces/%s"
    _space_id = None
    _name = None
    _description = None
    _space_type = None
    _space_status = None
    _custom = None
    _operation_type = None
    _operation_name = None
    _operation_http_method = None

    def __init__(self, pubnub, space_id, name: str = None, description: str = None, space_type: str = None,
                 space_status: str = None, custom: dict = None):
        EntitiesEndpoint.__init__(self, pubnub)

        self._space_id = str(space_id)
        if name is not None:
            self._name = str(name)

        if description is not None:
            self._description = str(description)

        if custom is not None:
            self._custom = dict(custom) if custom else None
            self._include_custom = True

        if space_type is not None:
            self._space_type = str(space_type)
            self._include_type = True

        if space_status is not None:
            self._space_status = str(space_status)
            self._include_status = True

    def _validate_space_id(self):
        if self._space_id is None or len(self._space_id) == 0:
            raise PubNubException(pn_error=PNERR_SPACE_MISSING)

    def build_path(self):
        return self.SPACE_PATH % (self.pubnub.config.subscribe_key, self._space_id)

    def build_data(self):
        payload = {}

        if self._name:
            payload['name'] = self._name
        if self._description:
            payload['description'] = self._description
        if self._custom:
            payload['custom'] = self._custom
        if self._space_status:
            payload['status'] = self._space_status
        if self._space_type:
            payload['type'] = self._space_type

        return write_value_as_string(payload)

    def validate_specific_params(self):
        self._validate_space_id()

    def operation_type(self):
        return self._operation_type

    def name(self):
        return self._operation_name

    def http_method(self):
        return self._operation_http_method


class CreateSpace(EntitiesSpaceEndpoint):
    def __init__(self, pubnub, space_id, name: str = None, description: str = None, space_type: str = None,
                 space_status: str = None, custom: dict = None):
        super().__init__(pubnub, space_id, name, description, space_type, space_status, custom)

        self._operation_type = PNOperationType.PNCreateSpaceOperation
        self._operation_name = "Create Space V3"
        self._operation_http_method = HttpMethod.POST

    def create_response(self, envelope) -> PNCreateSpaceResult:
        return PNCreateSpaceResult(envelope)


class UpdateSpace(EntitiesSpaceEndpoint):
    def __init__(self, pubnub, space_id, name: str = None, description: str = None, space_type: str = None,
                 space_status: str = None, custom: dict = None):
        super().__init__(pubnub, space_id, name, description, space_type, space_status, custom)

        self._operation_type = PNOperationType.PNUpdateSpaceOperation
        self._operation_name = "Update Space V3"
        self._operation_http_method = HttpMethod.PATCH
        self._custom_headers = {"Content-type": "application/json"}

    def create_response(self, envelope) -> PNUpdateSpaceResult:
        return PNUpdateSpaceResult(envelope)


class UpsertSpace(EntitiesSpaceEndpoint):
    def __init__(self, pubnub, space_id, name: str = None, description: str = None, space_type: str = None,
                 space_status: str = None, custom: dict = None):
        super().__init__(pubnub, space_id, name, description, space_type, space_status, custom)

        self._operation_type = PNOperationType.PNUpsertSpaceOperation
        self._operation_name = "Upsert Space V3"
        self._operation_http_method = HttpMethod.PUT
        self._custom_headers = {"Content-type": "application/json"}

    def create_response(self, envelope) -> PNUpsertSpaceResult:
        return PNUpsertSpaceResult(envelope)


class RemoveSpace(EntitiesSpaceEndpoint):
    def __init__(self, pubnub, space_id: str):
        super().__init__(pubnub, space_id)

        self._operation_type = PNOperationType.PNRemoveSpaceOperation
        self._operation_name = "Remove Space V3"
        self._operation_http_method = HttpMethod.DELETE

    def create_response(self, envelope):
        return PNRemoveSpaceResult(envelope)

    def build_data(self):
        return ''


class FetchSpace(EntitiesSpaceEndpoint):
    def __init__(self, pubnub, space_id: str, include: list = []):
        super().__init__(pubnub, space_id)

        self._operation_type = PNOperationType.PNFetchSpaceOperation
        self._operation_name = "Fetch Space V3"

        self._operation_http_method = HttpMethod.GET

        if 'custom' in include:
            self._include_custom = True

        if 'status' in include:
            self._include_status = True

        if 'type' in include:
            self._include_type = True

    def create_response(self, envelope):
        return PNFetchSpaceResult(envelope)

    def build_data(self):
        return ''


class FetchSpaces(EntitiesEndpoint):
    SPACE_PATH = "/v3/objects/%s/spaces"

    def __init__(self, pubnub, limit: str = None, filter_string: str = None, include_total_count: bool = None,
                 include_custom: bool = None, page: PNPage = None, sort_keys=None):
        super().__init__(pubnub)

        self._limit = limit
        self._filter = filter_string
        self._include_total_count = include_total_count
        self._sort_keys = sort_keys
        self._page = page
        self._include_custom = include_custom

    def build_path(self):
        return self.SPACE_PATH % self.pubnub.config.subscribe_key

    def create_response(self, envelope):
        return PNFetchSpacesResult(envelope)

    def operation_type(self):
        return PNOperationType.PNFetchSpacesOperation

    def name(self):
        return "Fetch Spaces"

    def http_method(self):
        return HttpMethod.GET

    def custom_params(self):
        params = {}
        inclusions = []

        if self._include_custom:
            inclusions.append("custom")

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
