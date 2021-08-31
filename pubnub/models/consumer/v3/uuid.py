from pubnub.models.consumer.v3.pn_resource import PNResource


class UUID(PNResource):

    def __init__(self, resource_name=None, resource_pattern=None):
        super(UUID, self).__init__(resource_name, resource_pattern)

    @staticmethod
    def id(user_id):
        user = UUID(resource_name=user_id)
        return user

    @staticmethod
    def pattern(user_pattern):
        user = UUID(resource_pattern=user_pattern)
        return user

    def delete(self):
        self._delete = True
        return self

    def get(self):
        self._get = True
        return self

    def update(self):
        self._update = True
        return self
