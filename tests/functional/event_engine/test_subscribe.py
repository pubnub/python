from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio, EventEngineSubscriptionManager, SubscribeCallback
from pubnub.event_engine.models import states


def test_subscribe_triggers_event():
    config = PNConfiguration()
    config.publish_key = 'demo'
    config.subscribe_key = 'demo'
    config.user_id = 'demo'

    pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager)

    callback = SubscribeCallback()
    pubnub.add_listener(callback)

    pubnub.subscribe().channels('foo').execute()
    assert pubnub._subscription_manager.event_engine.get_state_name() == states.ReceivingState.__name__


# def test_subscribe_with_tt_triggers_event():
#     config = PNConfiguration()
#     config.publish_key = 'demo'
#     config.subscribe_key = 'demo'
#     config.user_id = 'demo'
#     pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager)

#     callback = SubscribeCallback()
#     pubnub.add_listener(callback)

#     pubnub.subscribe().channels('foo').with_timetoken(123).execute()
#     assert pubnub._subscription_manager.event_engine.get_state_name() == states.ReceivingState.__name__
