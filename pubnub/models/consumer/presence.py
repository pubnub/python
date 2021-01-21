class PNHereNowResult:
    def __init__(self, total_channels, total_occupancy, channels):
        assert isinstance(total_channels, int)
        assert isinstance(total_occupancy, int)

        self.total_channels = total_channels
        self.total_occupancy = total_occupancy
        self.channels = channels

    def __str__(self):
        return "HereNow Result total occupancy: %d, total channels: %d" % (self.total_occupancy, self.total_channels)

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
                if isinstance(user, str):
                    occupants.append(PNHereNowOccupantsData(user, None))
                else:
                    state = user['state'] if 'state' in user else None
                    occupants.append(PNHereNowOccupantsData(user['uuid'], state))

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

    def __str__(self):
        return "HereNow Channel Data for channel '%s': occupancy: %d, occupants: %d" \
               % (self.channel_name, self.occupancy, self.occupants)

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

    def __str__(self):
        return "HereNow Occupants Data for '%s': %s" % (self.uuid, self.state)


class PNWhereNowResult(object):
    def __init__(self, channels):
        assert isinstance(channels, (list, tuple))
        self.channels = channels

    def __str__(self):
        return "User is currently subscribed to %s" % ", ".join(self.channels)

    @classmethod
    def from_json(cls, json_input):
        return PNWhereNowResult(json_input['payload']['channels'])


class PNSetStateResult(object):
    def __init__(self, state):
        assert isinstance(state, dict)
        self.state = state

    def __str__(self):
        return "New state %s successfully set" % self.state


class PNGetStateResult(object):
    def __init__(self, channels):
        assert isinstance(channels, dict)
        self.channels = channels

    def __str__(self):
        return "Current state is %s" % self.channels
