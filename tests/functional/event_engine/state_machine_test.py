from pubnub.event_engine import effects, events, states
from pubnub.event_engine.statemachine import StateMachine


def test_initialize_with_state():
    machine = StateMachine(states.UnsubscribedState)
    assert states.UnsubscribedState.__name__ == machine.get_state_name()


def test_unsubscribe_state_trigger_sub_changed():
    machine = StateMachine(states.UnsubscribedState)
    transition_effects = machine.trigger(events.SubscriptionChangedEvent(
        channels=['test'], groups=[]
    ))

    assert len(transition_effects) == 1
    assert isinstance(transition_effects[0], effects.HandshakeEffect)
    assert states.HandshakingState.__name__ == machine.get_state_name()


def test_unsubscribe_state_trigger_sub_restored():
    machine = StateMachine(states.UnsubscribedState)
    transition_effects = machine.trigger(events.SubscriptionChangedEvent(
        channels=['test'], groups=[]
    ))

    assert len(transition_effects) == 1
    assert isinstance(transition_effects[0], effects.HandshakeEffect)
    assert states.HandshakingState.__name__ == machine.get_state_name()
