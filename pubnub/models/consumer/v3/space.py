from pubnub.models.consumer.v3.pn_resource import PNResource


class Space(PNResource):

    def __init__(self, resource_name=None, resource_pattern=None):
        super(Space, self).__init__(resource_name, resource_pattern)

    @staticmethod
    def id(space_id):
        space = Space(resource_name=space_id)
        return space

    @staticmethod
    def pattern(space_pattern):
        space = Space(resource_pattern=space_pattern)
        return space

    def read(self):
        self._read = True
        return self

    def write(self):
        self._write = True
        return self

    def create(self):
        self._create = True
        return self

    def manage(self):
        self._manage = True
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
