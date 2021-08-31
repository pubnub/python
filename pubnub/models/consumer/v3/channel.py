from pubnub.models.consumer.v3.pn_resource import PNResource


class Channel(PNResource):

    def __init__(self, resource_name=None, resource_pattern=None):
        super(Channel, self).__init__(resource_name, resource_pattern)

    @staticmethod
    def id(channel_id):
        channel = Channel(resource_name=channel_id)
        return channel

    @staticmethod
    def pattern(channel_pattern):
        channel = Channel(resource_pattern=channel_pattern)
        return channel

    def read(self):
        self._read = True
        return self

    def manage(self):
        self._manage = True
        return self

    def write(self):
        self._write = True
        return self

    def delete(self):
        self._delete = True
        return self

    def get(self):
        self._get = True
        return self

    def update(self):
        self._update = True
        return self

    def join(self):
        self._join = True
        return self
