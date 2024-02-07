class PresenceStateContainer:
    channel_states: dict

    def __init__(self):
        self.channel_states = {}

    def register_state(self, state: dict, channels: list):
        for channel in channels:
            self.channel_states[channel] = state

    def get_state(self, channels: list):
        return {channel: self.channel_states[channel] for channel in channels if channel in self.channel_states}

    def get_channels_states(self, channels: list):
        return {channel: self.channel_states[channel] for channel in channels if channel in self.channel_states}
