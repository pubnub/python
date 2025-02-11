from json import loads, JSONDecodeError


class PubNubException(Exception):
    def __init__(self, errormsg="", status_code=0, pn_error=None, status=None):
        self._errormsg = errormsg
        self._status_code = status_code
        self._pn_error = pn_error
        self.status = status

        if len(str(errormsg)) > 0 and int(status_code) > 0:
            msg = str(pn_error) + " (" + str(status_code) + "): " + str(errormsg)
        elif len(str(errormsg)) > 0:
            msg = str(pn_error) + ": " + str(errormsg)
        else:
            msg = str(pn_error)

        super(PubNubException, self).__init__(msg)

    @property
    def _status(self):
        raise DeprecationWarning
        return self.status

    def get_status_code(self):
        return self._status_code

    def get_error_message(self):
        try:
            error = loads(self._errormsg)
            return error.get('error')
        except JSONDecodeError:
            return self._errormsg


class PubNubAsyncioException(Exception):
    def __init__(self, result, status):
        self.result = result
        self.status = status

    def __str__(self):
        return str(self.status.error_data.exception)

    @staticmethod
    def is_error():
        return True

    def value(self):
        return self.status.error_data.exception
