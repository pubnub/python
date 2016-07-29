import six

from .enums import HttpMethod


class RequestOptions(object):
    def __init__(self, path, params, method, request_timeout, connect_timeout, create_response,
                 create_status, data=None, sort_arguments=False):
        assert len(path) > 0
        assert isinstance(params, dict)
        assert isinstance(method, six.integer_types)
        assert isinstance(request_timeout, six.integer_types)
        assert isinstance(connect_timeout, six.integer_types)
        assert method is HttpMethod.GET or method is HttpMethod.POST

        self.path = path
        self.params = params
        self._method = method
        self.request_timeout = request_timeout
        self.connect_timeout = connect_timeout
        # TODO: rename to 'body'
        self.data = data
        self.sort_params = sort_arguments

        self.create_response = create_response
        self.create_status = create_status

    @property
    def method_string(self):
        return HttpMethod.string(self._method)

    def is_post(self):
        return self._method is HttpMethod.POST

    def query_list(self):
        """ All query keys and values should be already encoded inside a build_params() method"""
        s = []

        for k, v in self.params.items():
            s.append(str(k) + "=" + str(v))

        if self.sort_params:
            return sorted(s)
        else:
            return s

    @property
    def query_string(self):
        return str('&'.join(self.query_list()))


class PlatformOptions(object):
    def __init__(self, headers, scheme_and_host):
        self.headers = headers
        self.scheme_and_host = scheme_and_host


class ResponseInfo(object):
    def __init__(self, status_code, tls_enabled, origin, uuid, auth_key, client_request):
        self.status_code = status_code
        self.tls_enabled = tls_enabled
        self.origin = origin
        self.uuid = uuid
        self.auth_key = auth_key
        self.client_request = client_request


class Envelope(object):
    def __init__(self, result, status):
        self.result = result
        self.status = status
