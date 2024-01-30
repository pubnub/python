class SubscribeOperation(object):
    def __init__(self, channels=None, channel_groups=None, presence_enabled=None, timetoken=None):
        assert isinstance(channels, (list, tuple))
        assert isinstance(channel_groups, (list, tuple))
        assert isinstance(presence_enabled, bool)
        assert isinstance(timetoken, int)

        self.channels = channels
        self.channel_groups = channel_groups
        self.presence_enabled = presence_enabled
        self.timetoken = timetoken

    @property
    def channels_with_pressence(self):
        if not self.presence_enabled:
            return self.channels
        return [*self.channels] + [ch + '-pnpres' for ch in self.channels]

    @property
    def groups_with_pressence(self):
        if not self.presence_enabled:
            return self.channel_groups
        return [*self.channel_groups] + [ch + '-pnpres' for ch in self.channel_groups]


class UnsubscribeOperation(object):
    def __init__(self, channels=None, channel_groups=None):
        assert isinstance(channels, (list, tuple))
        assert isinstance(channel_groups, (list, tuple))

        self.channels = channels
        self.channel_groups = channel_groups


class StateOperation(object):
    def __init__(self, channels=None, channel_groups=None, state=None):
        self.channels = channels
        self.channel_groups = channel_groups
        self.state = state
