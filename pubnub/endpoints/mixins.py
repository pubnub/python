from pubnub.errors import PNERR_UUID_MISSING
from pubnub.exceptions import PubNubException


class UUIDValidatorMixin:
    def validate_uuid(self):
        if self._uuid is None or not isinstance(self._uuid, str):
            raise PubNubException(pn_error=PNERR_UUID_MISSING)


class TimeTokenOverrideMixin:
    def replicate(self, replicate):
        self._replicate = replicate
        return self

    def ptto(self, timetoken):
        if timetoken:
            assert isinstance(timetoken, int)
            self._ptto = timetoken
        return self

    def custom_params(self):
        params = {}
        if self._replicate is not None:
            if self._replicate:
                params["norep"] = "false"
            else:
                params["norep"] = "true"

        if self._ptto:
            params["ptto"] = self._ptto

        return params
