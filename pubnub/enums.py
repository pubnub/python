class HttpMethod(object):
    GET = 1
    POST = 2

    @classmethod
    def string(cls, method):
        if method == cls.GET:
            return "GET"
        elif method == cls.POST:
            return "POST"
