import unittest

from pubnub.models.consumer.presence import PNHereNowResult

empty = {'service': 'Presence', 'status': 200, 'message': 'OK', 'occupancy': 0, 'uuids': []}
empty_disable_uuids = {'message': 'OK', 'occupancy': 0, 'status': 200, 'service': 'Presence'}

single = {'status': 200, 'message': 'OK', 'service': 'Presence', 'occupancy': 1,
          'uuids': ['08c36f36-7b00-41c9-b101-d07b19bc30cb']}
single_disable_uuids = {'service': 'Presence', 'occupancy': 1, 'message': 'OK', 'status': 200}
single_with_state = {'uuids': [{'uuid': 'c190fbdc-dcde-4553-9085-85f8dedf76e4'}], 'status': 200, 'occupancy': 1,
                     'service': 'Presence', 'message': 'OK'}

multiple = {'status': 200, 'message': 'OK', 'payload': {'total_channels': 2, 'channels': {
    'here-now-GIY92DGX': {'occupancy': 1, 'uuids': ['c71b2961-9624-4801-90bc-6c89a725a422']},
    'here-now-B1WZA4LO': {'occupancy': 1, 'uuids': ['c71b2961-9624-4801-90bc-6c89a725a422']}}, 'total_occupancy': 2},
            'service': 'Presence'}
multiple_with_state_disable_uuids = {
    'payload': {'channels': {'here-now-IUX5HV7O': {'occupancy': 1}, 'here-now-FGE5Q9UY': {'occupancy': 1}},
                'total_occupancy': 2, 'total_channels': 2}, 'message': 'OK', 'service': 'Presence', 'status': 200}
multiple_with_state = {'payload': {'total_occupancy': 2, 'channels': {
    'here-now-16IAN0F9': {'occupancy': 1, 'uuids': [{'uuid': 'd66b4e96-8972-4f1d-9942-46dd60947d85'}]},
    'here-now-249XRUPW': {'occupancy': 1, 'uuids': [{'uuid': 'd66b4e96-8972-4f1d-9942-46dd60947d85'}]}},
                                   'total_channels': 2}, 'service': 'Presence', 'status': 200, 'message': 'OK'}


class TestHereNowResultGenerator(unittest.TestCase):
    def test_empty(self):
        channel_names = ['blah']
        response = PNHereNowResult.from_json(empty, channel_names)
        channels = response.channels

        assert response.total_channels == 1
        assert response.total_occupancy == 0
        assert isinstance(channels, list)
        assert len(channels) == 0

    def test_empty_disable_uuids(self):
        channel_names = ['blah']
        response = PNHereNowResult.from_json(empty_disable_uuids, channel_names)
        channels = response.channels

        assert response.total_channels == 1
        assert response.total_occupancy == 0
        assert isinstance(channels, list)
        assert len(channels) == 0

    def test_single(self):
        channel_names = ['blah']
        response = PNHereNowResult.from_json(single, channel_names)
        channels = response.channels

        assert response.total_channels == 1
        assert response.total_occupancy == 0
        assert isinstance(channels, list)
        assert len(channels) == 0