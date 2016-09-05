import unittest

from pubnub.models.consumer.presence import PNHereNowResult

empty = {'service': 'Presence', 'status': 200, 'message': 'OK', 'occupancy': 0, 'uuids': []}
empty_disable_uuids = {'message': 'OK', 'occupancy': 0, 'status': 200, 'service': 'Presence'}
empty_multiple = {'service': 'Presence', 'status': 200, 'payload': {
    'total_channels': 0, 'total_occupancy': 0, 'channels': {}}, 'message': 'OK'}

single = {'status': 200, 'message': 'OK', 'service': 'Presence', 'occupancy': 1,
          'uuids': ['08c36f36-7b00-41c9-b101-d07b19bc30cb']}
single_disable_uuids = {'service': 'Presence', 'occupancy': 1, 'message': 'OK', 'status': 200}
single_with_state = {'status': 200, 'message': 'OK', 'occupancy': 1, 'service': 'Presence',
                     'uuids': [{'state': {'count': 5, 'name': 'Alex'}, 'uuid': '6cbb18b9-3f58-4bd3-91c0-5dbf18a4af13'}]}

multiple = {'status': 200, 'message': 'OK', 'payload': {'total_channels': 2, 'channels': {
    'here-now-GIY92DGX': {'occupancy': 1, 'uuids': ['c71b2961-9624-4801-90bc-6c89a725a422']},
    'here-now-B1WZA4LO': {'occupancy': 1, 'uuids': ['c71b2961-9624-4801-90bc-6c89a725a422']}}, 'total_occupancy': 2},
    'service': 'Presence'}
multiple_disable_uuids = {
    'payload': {'channels': {'here-now-IUX5HV7O': {'occupancy': 1}, 'here-now-FGE5Q9UY': {'occupancy': 1}},
                'total_occupancy': 2, 'total_channels': 2}, 'message': 'OK', 'service': 'Presence', 'status': 200}
multiple_with_state = {'payload': {'total_channels': 2, 'channels': {
    'here-now-UBJJ5P3W': {
        'uuids': [{'state': {'count': 5, 'name': 'Alex'}, 'uuid': 'abf41ee8-0853-4e1c-8450-906933695b09'}],
        'occupancy': 1
    },
    'here-now-EZTFTHZY': {'uuids': [{'uuid': 'abf41ee8-0853-4e1c-8450-906933695b09'}], 'occupancy': 1}},
    'total_occupancy': 2}, 'status': 200, 'message': 'OK', 'service': 'Presence'}


class TestHereNowResultGenerator(unittest.TestCase):
    def test_empty_occupancy(self):
        channel_names = ['blah']
        response = PNHereNowResult.from_json(empty, channel_names)
        channels = response.channels

        assert response.total_channels == 1
        assert response.total_occupancy == 0
        assert isinstance(channels, list)
        assert len(channels) == 1

    def test_empty_disable_uuids(self):
        channel_names = ['blah']
        response = PNHereNowResult.from_json(empty_disable_uuids, channel_names)
        channels = response.channels

        assert response.total_channels == 1
        assert response.total_occupancy == 0
        assert isinstance(channels, list)
        assert len(channels) == 1

    def test_empty_multiple(self):
        channel_names = ['blah']
        response = PNHereNowResult.from_json(empty_multiple, channel_names)
        channels = response.channels

        assert response.total_channels == 1
        assert response.total_occupancy == 0
        assert isinstance(channels, list)
        assert len(channels) == 1

    def test_single(self):
        channel_names = ['blah']
        response = PNHereNowResult.from_json(single, channel_names)
        channels = response.channels

        assert response.total_channels == 1
        assert response.total_occupancy == 1
        assert isinstance(channels, list)
        assert len(channels) == 1

        channel = channels[0]

        assert channel.channel_name == 'blah'
        assert channel.occupancy == 1
        assert len(channel.occupants) == 1

        occupants = channel.occupants[0]

        assert occupants.state is None
        assert occupants.uuid == single['uuids'][0]

    def test_single_disable_uuids(self):
        channel_names = ['blah']
        response = PNHereNowResult.from_json(single_disable_uuids, channel_names)
        channels = response.channels

        assert response.total_channels == 1
        assert response.total_occupancy == 1
        assert isinstance(channels, list)
        assert len(channels) == 1

        channel = channels[0]

        assert channel.channel_name == 'blah'
        assert channel.occupancy == 1
        assert len(channel.occupants) == 0

    def test_single_with_state(self):
        channel_names = ['blah']
        response = PNHereNowResult.from_json(single_with_state, channel_names)
        channels = response.channels

        assert response.total_channels == 1
        assert response.total_occupancy == 1
        assert isinstance(channels, list)
        assert len(channels) == 1

        channel = channels[0]

        assert channel.channel_name == 'blah'
        assert channel.occupancy == 1
        assert len(channel.occupants) == 1

        occupants = channel.occupants[0]

        assert occupants.uuid == single_with_state['uuids'][0]['uuid']
        assert occupants.state == single_with_state['uuids'][0]['state']

    def test_multiple(self):
        channel_names = list(multiple['payload']['channels'])
        response = PNHereNowResult.from_json(multiple, channel_names)
        channels = response.channels

        assert response.total_channels == 2
        assert response.total_occupancy == 2
        assert isinstance(channels, list)
        assert len(channels) == 2

        channel1 = channels[0]

        assert channel1.channel_name == channel_names[0]
        assert channel1.occupancy == multiple['payload']['channels'][channel_names[0]]['occupancy']
        assert len(channel1.occupants) == 1

        occupants = channel1.occupants[0]

        assert occupants.state is None
        assert occupants.uuid == multiple['payload']['channels'][channel_names[0]]['uuids'][0]

        channel2 = channels[1]

        assert channel2.channel_name == channel_names[1]
        assert channel2.occupancy == multiple['payload']['channels'][channel_names[1]]['occupancy']
        assert len(channel2.occupants) == 1

        occupants = channel2.occupants[0]

        assert occupants.state is None
        assert occupants.uuid == multiple['payload']['channels'][channel_names[1]]['uuids'][0]

    def test_multiple_disable_uuids(self):
        channel_names = list(multiple_disable_uuids['payload']['channels'])
        response = PNHereNowResult.from_json(multiple_disable_uuids, channel_names)
        channels = response.channels

        assert response.total_channels == 2
        assert response.total_occupancy == 2
        assert isinstance(channels, list)
        assert len(channels) == 2

        channel1 = channels[0]

        assert channel1.channel_name == channel_names[0]
        assert channel1.occupancy == multiple_disable_uuids['payload']['channels'][channel_names[0]]['occupancy']
        assert channel1.occupants is None

        channel2 = channels[1]

        assert channel2.channel_name == channel_names[1]
        assert channel2.occupancy == multiple_disable_uuids['payload']['channels'][channel_names[1]]['occupancy']
        assert channel2.occupants is None

    def test_multiple_with_state(self):
        channel_names = list(reversed(sorted(list(multiple_with_state['payload']['channels']))))
        response = PNHereNowResult.from_json(multiple_with_state, channel_names)
        channels = response.channels

        assert response.total_channels == 2
        assert response.total_occupancy == 2
        assert isinstance(channels, list)
        assert len(channels) == 2

        if channels[0].channel_name == channel_names[0]:
            channel1 = channels[0]
            channel2 = channels[1]
        else:
            channel1 = channels[1]
            channel2 = channels[0]

        assert channel1.channel_name == channel_names[0]
        assert channel1.occupancy == multiple_with_state['payload']['channels'][channel1.channel_name]['occupancy']
        assert len(channel1.occupants) == 1

        occupants = channel1.occupants[0]

        assert occupants.state['name'] == "Alex"
        assert occupants.state['count'] == 5
        assert occupants.uuid == multiple_with_state['payload']['channels'][channel1.channel_name]['uuids'][0]['uuid']

        assert channel2.channel_name == channel_names[1]
        assert channel2.occupancy == multiple_with_state['payload']['channels'][channel2.channel_name]['occupancy']
        assert len(channel2.occupants) == 1

        occupants = channel2.occupants[0]

        assert occupants.state is None
        assert occupants.uuid == multiple_with_state['payload']['channels'][channel2.channel_name]['uuids'][0]['uuid']
