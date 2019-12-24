from pubnub.models.consumer.v3.pn_resource import PNResource


class Group(PNResource):

    def __init__(self, resource_name=None, resource_pattern=None):
        super(Group, self).__init__(resource_name, resource_pattern)

    @staticmethod
    def id(group_id):
        group = Group(resource_name=group_id)
        return group

    @staticmethod
    def pattern(group_pattern):
        group = Group(resource_pattern=group_pattern)
        return group

    def read(self):
        self._read = True
        return self

    def manage(self):
        self._manage = True
        return self
