import six


class PNHereNowResult(object):
    def __init__(self, total_channels, total_occupancy, channels):
        assert isinstance(total_channels, six.integer_types)
        assert isinstance(total_occupancy, six.integer_types)

        self.total_channels = total_channels
        self.total_occupancy = total_occupancy
        self.channels = channels

    @classmethod
    def from_json(cls, envelope, channel_names):
        # multiple
        if 'payload' in envelope and isinstance(envelope['payload'], dict):
            json_input = envelope['payload']

            channels = []
            if len(json_input['channels']) > 0:
                for channel_name, raw_data in json_input['channels'].items():
                    channels.append(PNHereNowChannelData.from_json(channel_name, raw_data))
                return PNHereNowResult(
                    total_channels=int(json_input['total_channels']),
                    total_occupancy=int(json_input['total_occupancy']),
                    channels=channels)
            elif len(channel_names) == 1:
                return PNHereNowResult(
                    total_channels=int(1),
                    total_occupancy=int(json_input['total_occupancy']),
                    channels=[PNHereNowChannelData(channel_names[0], 0, [])]
                )
            else:
                return PNHereNowResult(
                    total_channels=int(json_input['total_channels']),
                    total_occupancy=int(json_input['total_occupancy']),
                    channels={}
                )
        # empty
        elif 'occupancy' in envelope and int(envelope['occupancy']) == 0:
            return PNHereNowResult(
                total_channels=int(1),
                total_occupancy=int(envelope['occupancy']),
                channels=[PNHereNowChannelData(channel_names[0], 0, [])]
            )
        # single
        elif 'uuids' in envelope and isinstance(envelope['uuids'], list):
            occupants = []
            for user in envelope['uuids']:
                if isinstance(user, six.string_types):
                    occupants.append(PNHereNowOccupantsData(user, None))
                else:
                    occupants.append(PNHereNowOccupantsData(user['uuid'], user['state']))

            return PNHereNowResult(
                total_channels=1,
                total_occupancy=int(envelope['occupancy']),
                channels=[
                    PNHereNowChannelData(
                        channel_name=channel_names[0],
                        occupancy=envelope['occupancy'],
                        occupants=occupants
                    )
                ])
        else:
            return PNHereNowResult(
                total_channels=1,
                total_occupancy=int(envelope['occupancy']),
                channels=[
                    PNHereNowChannelData(
                        channel_name=channel_names[0],
                        occupancy=envelope['occupancy'],
                        occupants=[]
                    )
                ])


class PNHereNowChannelData(object):
    def __init__(self, channel_name, occupancy, occupants):
        self.channel_name = channel_name
        self.occupancy = occupancy
        self.occupants = occupants

    @classmethod
    def from_json(cls, name, json_input):
        if 'uuids' in json_input:
            occupants = []
            for user in json_input['uuids']:
                if isinstance(user, dict) and len(user) > 0:
                    if 'state' in user:
                        occupants.append(PNHereNowOccupantsData(user['uuid'], user['state']))
                    else:
                        occupants.append(PNHereNowOccupantsData(user['uuid'], None))
                else:
                    occupants.append(PNHereNowOccupantsData(user, None))
        else:
            occupants = None

        return PNHereNowChannelData(
            channel_name=name,
            occupancy=int(json_input['occupancy']),
            occupants=occupants
        )


class PNHereNowOccupantsData(object):
    def __init__(self, uuid, state):
        self.uuid = uuid
        self.state = state


class PNWhereNowResult(object):
    def __init__(self, channels):
        assert isinstance(channels, (list, tuple))
        self.channels = channels

    @classmethod
    def from_json(cls, json_input):
        return PNWhereNowResult(json_input['payload']['channels'])


class PNSetStateResult(object):
    def __init__(self, state):
        assert isinstance(state, dict)
        self.state = state


class PNGetStateResult(object):
    def __init__(self, channels):
        assert isinstance(channels, dict)
        self.channels = channels
