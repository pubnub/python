import six

from pubnub.errors import PNERR_UUID_MISSING
from pubnub.exceptions import PubNubException


class UUIDValidatorMixin:
    def validate_uuid(self):
        if self._uuid is None or not isinstance(self._uuid, six.string_types):
            raise PubNubException(pn_error=PNERR_UUID_MISSING)
