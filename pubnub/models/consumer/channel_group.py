class PNChannelGroupsAddChannelResult(object):
    pass


class PNChannelGroupsRemoveChannelResult(object):
    pass


class PNChannelGroupsRemoveGroupResult(object):
    pass


class PNChannelGroupsListResult(object):
    def __init__(self, channels):
        self.channels = channels
