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
        return self.channels + [ch + '-pnpres' for ch in self.channels]

    @property
    def groups_with_pressence(self):
        if not self.presence_enabled:
            return self.channel_groups
        return self.channel_groups + [ch + '-pnpres' for ch in self.channel_groups]


class UnsubscribeOperation(object):
    def __init__(self, channels=None, channel_groups=None):
        assert isinstance(channels, (list, tuple))
        assert isinstance(channel_groups, (list, tuple))

        self.channels = channels
        self.channel_groups = channel_groups

    def get_subscribed_channels(self, channels, with_presence=False) -> list:
        result = [ch for ch in channels if ch not in self.channels and not ch.endswith('-pnpres')]
        if not with_presence:
            return result
        return result + [ch + '-pnpres' for ch in result]

    def get_subscribed_channel_groups(self, channel_groups, with_presence=False) -> list:
        result = [grp for grp in channel_groups if grp not in self.channel_groups and not grp.endswith('-pnpres')]
        if not with_presence:
            return result
        return result + [grp + '-pnpres' for grp in result]


class StateOperation(object):
    def __init__(self, channels=None, channel_groups=None, state=None):
        self.channels = channels
        self.channel_groups = channel_groups
        self.state = state
