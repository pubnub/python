"""
Possible responses of PAMv3 request
"""


class _PAMv3Result(object):
    def __init__(self, token):
        self.token = token

    @classmethod
    def from_json(cls, json_input):
        return cls(
            token=json_input['token']
        )


class PNGrantTokenResult(_PAMv3Result):
    def __str__(self):
        return "Grant token: %s" % \
               (self.token)

    def get_token(self):
        return self.token


class PNRevokeTokenResult:
    def __init__(self, result):
        self.status = result['status']

    def __str__(self):
        return "Revoke token success with status: %s" % self.status
