from pubnub.event_engine.models import events, states
from pubnub.event_engine.statemachine import StateMachine


def test_initialize_with_state():
    machine = StateMachine(states.UnsubscribedState)
    assert states.UnsubscribedState.__name__ == machine.get_state_name()


def test_unsubscribe_state_trigger_sub_changed():
    machine = StateMachine(states.UnsubscribedState)
    machine.trigger(events.SubscriptionChangedEvent(
        channels=['test'], groups=[]
    ))
    assert states.HandshakingState.__name__ == machine.get_state_name()


def test_unsubscribe_state_trigger_sub_restored():
    machine = StateMachine(states.UnsubscribedState)
    machine.trigger(events.SubscriptionChangedEvent(
        channels=['test'], groups=[]
    ))
    assert states.HandshakingState.__name__ == machine.get_state_name()
