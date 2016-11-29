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
