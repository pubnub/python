from pubnub.endpoints.entities.endpoint import EntitiesEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.errors import PNERR_USER_ID_MISSING
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.entities.page import Next, Previous
from pubnub.models.consumer.entities.user import PNCreateUserResult, PNFetchUserResult, PNFetchUsersResult, \
    PNRemoveUserResult, PNUpdateUserResult, PNUpsertUserResult
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.utils import write_value_as_string


class EntitiesUserEndpoint(EntitiesEndpoint):
    USER_PATH = "/v3/objects/%s/users/%s"

    def __init__(self, pubnub, user_id: str, name: str = None, email: str = None, external_id: str = None,
                 profile_url: str = None, user_type: str = None, user_status: str = None, custom: dict = None):
        EntitiesEndpoint.__init__(self, pubnub)
        self._operation_type = None
        self._operation_name = None
        self._operation_http_method = None

        self._user_id = str(user_id)
        self._name = str(name)
        self._email = str(email)
        self._external_id = str(external_id)
        self._profile_url = str(profile_url)
        self._user_type = str(user_type)
        self._user_status = str(user_status)
        self._custom = dict(custom) if custom else None

        if custom is not None:
            self._custom = custom
            self._include_custom = True

        if user_status is not None:
            self._user_status = user_status
            self._include_status = True

        if user_type is not None:
            self._user_type = user_type
            self._include_type = True

    def _effective_user_id(self):
        if self._user_id is not None:
            return self._user_id
        else:
            return self.pubnub.config.user_id

    def _validate_user_id(self):
        if self._effective_user_id() is None or len(self._effective_user_id()) == 0:
            raise PubNubException(pn_error=PNERR_USER_ID_MISSING)

    def build_path(self):
        return self.USER_PATH % (self.pubnub.config.subscribe_key, self._effective_user_id())

    def build_data(self):
        payload = {
            "name": self._name,
            "email": self._email,
            "externalId": self._external_id,
            "profileUrl": self._profile_url,
            "custom": self._custom,
            "status": self._user_status,
            "type": self._user_type,
        }
        return write_value_as_string(payload)

    def validate_specific_params(self):
        self._validate_user_id()

    def operation_type(self):
        return self._operation_type

    def name(self):
        return self._operation_name

    def http_method(self):
        return self._operation_http_method


class CreateUser(EntitiesUserEndpoint):
    def __init__(self, pubnub, user_id: str, name: str = None, email: str = None, external_id: str = None,
                 profile_url: str = None, user_type: str = None, user_status: str = None, custom: dict = None):
        super().__init__(pubnub, user_id, name, email, external_id, profile_url, user_type, user_status, custom)

        self._operation_type = PNOperationType.PNCreateUserOperation
        self._operation_name = "Create User V3"
        self._operation_http_method = HttpMethod.POST

    def create_response(self, envelope):
        return PNCreateUserResult(envelope)


class UpdateUser(EntitiesUserEndpoint):
    def __init__(self, pubnub, user_id: str, name: str = None, email: str = None, external_id: str = None,
                 profile_url: str = None, user_type: str = None, user_status: str = None, custom: dict = None):
        super().__init__(pubnub, user_id, name, email, external_id, profile_url, user_type, user_status, custom)

        self._operation_type = PNOperationType.PNUpdateUserOperation
        self._operation_name = "Update User V3"
        self._operation_http_method = HttpMethod.PATCH
        self._custom_headers = {"Content-type": "application/json"}

    def create_response(self, envelope):
        return PNUpdateUserResult(envelope)


class UpsertUser(EntitiesUserEndpoint):
    def __init__(self, pubnub, user_id: str, name: str = None, email: str = None, external_id: str = None,
                 profile_url: str = None, user_type: str = None, user_status: str = None, custom: dict = None):
        super().__init__(pubnub, user_id, name, email, external_id, profile_url, user_type, user_status, custom)

        self._operation_type = PNOperationType.PNUpsertUserOperation
        self._operation_name = "Upsert User V3"
        self._operation_http_method = HttpMethod.PUT
        self._custom_headers = {"Content-type": "application/json"}

    def create_response(self, envelope):
        return PNUpsertUserResult(envelope)


class RemoveUser(EntitiesUserEndpoint):
    def __init__(self, pubnub, user_id: str):
        super().__init__(pubnub, user_id)

        self._operation_type = PNOperationType.PNRemoveUserOperation
        self._operation_name = "Remove User V3"
        self._operation_http_method = HttpMethod.DELETE

    def create_response(self, envelope):
        return PNRemoveUserResult(envelope)

    def build_data(self):
        return ''


class FetchUser(EntitiesUserEndpoint):
    def __init__(self, pubnub, user_id: str, include: list = []):
        super().__init__(pubnub, user_id)

        self._operation_type = PNOperationType.PNFetchUserOperation
        self._operation_name = "Fetch User V3"
        self._operation_http_method = HttpMethod.GET

        if 'custom' in include:
            self._include_custom = True

        if 'status' in include:
            self._include_status = True

        if 'type' in include:
            self._include_type = True

    def create_response(self, envelope):
        return PNFetchUserResult(envelope)

    def build_data(self):
        return ''


class FetchUsers(EntitiesEndpoint):
    USER_PATH = "/v3/objects/%s/users"

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
        return self.USER_PATH % self.pubnub.config.subscribe_key

    def create_response(self, envelope):
        return PNFetchUsersResult(envelope)

    def operation_type(self):
        return PNOperationType.PNFetchUsersOperation

    def name(self):
        return "Fetch Users"

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
