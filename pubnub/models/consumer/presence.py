import six


class PNHereNowResult(object):
    def __init__(self, total_channels, total_occupancy, channels):
        assert isinstance(total_channels, six.integer_types)
        assert isinstance(total_occupancy, six.integer_types)

        self.total_channels = total_channels
        self.total_occupancy = total_occupancy
        self.channels = channels

    @classmethod
    def from_json(cls, envelope, channels):
        # multiple
        if 'channels' in envelope and isinstance(envelope['channels'], dict):
            json_input = envelope['payload']
            channels = []

            for channel_name, raw_data in json_input['channels'].items():
                channels.append(PNHereNowChannelData.from_json(channel_name, raw_data))
            return PNHereNowResult(int(json_input['total_channels']), int(json_input['total_occupancy']), channels)
        # empty
        elif 'occupancy' in envelope and int(envelope['occupancy']) == 0:
            return PNHereNowResult(int(1), int(envelope['occupancy']), [])
        # single
        elif 'uuids' in envelope and isinstance(envelope['uuids'], list):
            occupants = []
            for uuid in envelope['uuids']:
                occupants.append(
                    PNHereNowOccupantsData(channels[0], uuid))

            channels = [PNHereNowChannelData(channels[0],
                                             envelope['occupancy'],
                                             occupants)]

            return PNHereNowResult(1, int(envelope['occupancy']), channels)


class PNHereNowChannelData(object):
    def __init__(self, channel_name, occupancy, occupants):
        self.channel_name = channel_name
        self.occupancy = occupancy
        self.occupants = occupants

    @classmethod
    def from_json(cls, name, json_input):
        occupants = []

        if isinstance(json_input['uuids'], list):
            for uuid in json_input['uuids']:
                occupants.append(PNHereNowOccupantsData(uuid, None))
        elif isinstance(json_input['uuids'], dict):
            for uuid, state in json_input['uuids'].items():
                occupants.append(PNHereNowOccupantsData(uuid, state))

        return PNHereNowChannelData(
            channel_name=name,
            occupancy=int(json_input['occupancy']),
            occupants=occupants
        )


class PNHereNowOccupantsData(object):
    def __init__(self, uuid, state):
        self.uuid = uuid
        self.state = state
