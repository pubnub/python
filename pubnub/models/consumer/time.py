from datetime import date


class PNTimeResponse(object):
    MULTIPLIER = 10000000

    def __init__(self, server_response):
        assert isinstance(server_response, list)
        self.server_response = server_response
        self.value_as_string = str(server_response[0])
        self.value_as_int = server_response[0]

    def __int__(self):
        return self.value_as_int

    def __str__(self):
        return self.value_as_string

    def date_time(self):
        return date.fromtimestamp(self.value_as_int / PNTimeResponse.MULTIPLIER)
