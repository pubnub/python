from pubnub.endpoints.access.grant import Grant
from pubnub.enums import PNOperationType


class Revoke(Grant):
    def __init__(self, pubnub):
        Grant.__init__(self, pubnub)
        self._read = False
        self._write = False
        self._manage = False
        self._get = False
        self._update = False
        self._join = False

        self._sort_params = True

    def read(self, flag):
        raise NotImplementedError

    def write(self, flag):
        raise NotImplementedError

    def manage(self, flag):
        raise NotImplementedError

    def operation_type(self):
        return PNOperationType.PNAccessManagerRevoke

    def name(self):
        return "Revoke"
