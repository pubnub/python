import six

from .enums import HttpMethod


class RequestOptions(object):
    def __init__(self, path, params_callback, method, request_timeout, connect_timeout, create_response,
                 create_status, create_exception, operation_type, data=None, sort_arguments=False):
        assert len(path) > 0
        assert callable(params_callback)
        assert isinstance(method, six.integer_types)
        assert isinstance(request_timeout, six.integer_types)
        assert isinstance(connect_timeout, six.integer_types)
        assert method is HttpMethod.GET or method is HttpMethod.POST

        self.params = None
        self.path = path
        self.params_callback = params_callback
        self._method = method
        self.request_timeout = request_timeout
        self.connect_timeout = connect_timeout
        # TODO: rename 'data' => 'body'
        self.data = data
        self.body = data
        self.sort_params = sort_arguments

        self.create_response = create_response
        self.create_status = create_status
        self.create_exception = create_exception
        self.operation_type = operation_type

    def merge_params_in(self, params_to_merge_in):
        self.params = self.params_callback(params_to_merge_in)

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

    def __str__(self):
        return "path: {0}, qs: {1}".format(self.path, self.query_string)


class PlatformOptions(object):
    def __init__(self, headers, pn_config):
        self.headers = headers
        self.pn_config = pn_config


class ResponseInfo(object):
    def __init__(self, status_code, tls_enabled, origin, uuid, auth_key, client_request, client_response=None):
        self.status_code = status_code
        self.tls_enabled = tls_enabled
        self.origin = origin
        self.uuid = uuid
        self.auth_key = auth_key
        self.client_request = client_request
        self.client_response = client_response


class Envelope(object):
    def __init__(self, result, status):
        self.result = result
        self.status = status
