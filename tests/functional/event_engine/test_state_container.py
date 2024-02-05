from pubnub.event_engine.containers import PresenceStateContainer


def test_set_state():
    container = PresenceStateContainer()
    container.register_state(state={'state': 'active'}, channels=['c1', 'c2'])
    assert container.get_channels_states(['c1', 'c2']) == {'c1': {'state': 'active'}, 'c2': {'state': 'active'}}
    assert container.get_state(['c1']) == {'c1': {'state': 'active'}}


def test_set_state_with_overwrite():
    container = PresenceStateContainer()
    container.register_state(state={'state': 'active'}, channels=['c1'])
    container.register_state(state={'state': 'inactive'}, channels=['c1'])
    assert container.get_channels_states(['c1']) == {'c1': {'state': 'inactive'}}
    assert container.get_state(['c1', 'c2']) == {'c1': {'state': 'inactive'}}
