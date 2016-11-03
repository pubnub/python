
class PNPushAddChannelResult(object):
    pass


class PNPushRemoveChannelResult(object):
    pass


class PNPushRemoveAllChannelsResult(object):
    pass


class PNPushListProvisionsResult(object):
    def __init__(self, channels):
        self.channels = channels
