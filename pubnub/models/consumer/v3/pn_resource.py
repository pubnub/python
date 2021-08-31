class PNResource(object):

    def __init__(self, resource_name=None, resource_pattern=None):
        self._resource_name = resource_name
        self._resource_pattern = resource_pattern
        self._read = False
        self._write = False
        self._create = False
        self._manage = False
        self._delete = False
        self._get = False
        self._update = False
        self._join = False

    def is_pattern_resource(self):
        return self._resource_pattern is not None

    def get_id(self):
        if self.is_pattern_resource():
            return self._resource_pattern

        return self._resource_name

    def is_read(self):
        return self._read

    def is_write(self):
        return self._write

    def is_create(self):
        return self._create

    def is_manage(self):
        return self._manage

    def is_delete(self):
        return self._delete

    def is_get(self):
        return self._get

    def is_update(self):
        return self._update

    def is_join(self):
        return self._join
