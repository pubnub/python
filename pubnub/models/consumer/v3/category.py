from pubnub.models.consumer.v3.pn_resource import PNResource


class Category(PNResource):
    """Category-level permission for a whole App Context resource type."""

    CHANNELS = 'channels'
    UUIDS = 'uuids'

    def __init__(self, resource_name=None):
        super(Category, self).__init__(resource_name)

    @staticmethod
    def channels():
        return Category(resource_name=Category.CHANNELS)

    @staticmethod
    def uuids():
        return Category(resource_name=Category.UUIDS)

    def get(self):
        self._get = True
        return self
