class PNHereNowResult(object):
    def __init__(self, total_channels, total_occupancy, channels):
        self.total_channels = total_channels
        self.total_occupancy = total_occupancy
        self.channels = channels


class PNHereNowChannelData(object):
    def __init__(self, channel_name, occupancy, occupants):
        self.channel_name = channel_name
        self.occupancy = occupancy
        self.occupants = occupants


class PNOccupantsData(object):
    def __init__(self, uuid, state):
        self.uuid = uuid,
        self.state = state
