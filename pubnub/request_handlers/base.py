from abc import abstractmethod, ABCMeta


class BaseRequestHandler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def sync_request(self, platform_options, endpoint_call_options):
        pass
