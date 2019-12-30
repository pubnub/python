from pubnub.models.consumer.v3.pn_resource import PNResource


class User(PNResource):

    def __init__(self, resource_name=None, resource_pattern=None):
        super(User, self).__init__(resource_name, resource_pattern)

    @staticmethod
    def id(user_id):
        user = User(resource_name=user_id)
        return user

    @staticmethod
    def pattern(user_pattern):
        user = User(resource_pattern=user_pattern)
        return user

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
