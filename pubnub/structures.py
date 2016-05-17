# TODO: choose a better name for this module
from .enums import HttpMethod


class RequestOptions(object):
    def __init__(self, path, params, method, data=None):
        assert len(path) > 0
        assert len(params) > 0
        assert isinstance(method, int)
        assert method is HttpMethod.GET or method is HttpMethod.POST

        self.path = path
        self.params = params
        self.method = method
        self.data = data
