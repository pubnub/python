from pubnub.callbacks import SubscribeCallback
from pubnub.models.consumer.objects_v2.channel import PNChannelMetadataResult
from pubnub.models.consumer.objects_v2.memberships import PNMembershipResult
from pubnub.models.consumer.objects_v2.uuid import PNUUIDMetadataResult
from pubnub.models.consumer.pubsub import PNFileMessageResult, PNMessageResult
from pubnub.models.subscription import (
    PNSubscriptionRegistry, PNSubscriptionType, PubNubChannel, PubNubChannelGroup, PubNubSubscriptionSet,
    PubNubUserMetadata
)


class FakeSubscriptionManager:
    def __init__(self):
        self._timetoken = 0
        self.subscribe_operations = []
        self.unsubscribe_operations = []

    def adapt_subscribe_builder(self, subscribe_operation):
        self.subscribe_operations.append(subscribe_operation)

    def adapt_unsubscribe_builder(self, unsubscribe_operation):
        self.unsubscribe_operations.append(unsubscribe_operation)


class FakePubNub:
    def __init__(self):
        self._subscription_manager = FakeSubscriptionManager()
        self._subscription_registry = PNSubscriptionRegistry(self)
        self.listeners = []

    def add_listener(self, listener):
        self.listeners.append(listener)

    def channel(self, name):
        return PubNubChannel(self, name)

    def subscription_set(self, subscriptions):
        return PubNubSubscriptionSet(self, subscriptions)


class RecordingCallback(SubscribeCallback):
    def __init__(self):
        self.calls = []

    def status(self, pubnub, status):
        self.calls.append(('status', pubnub, status))

    def message(self, pubnub, message):
        self.calls.append(('message', pubnub, message))

    def presence(self, pubnub, presence):
        self.calls.append(('presence', pubnub, presence))

    def channel(self, pubnub, channel):
        self.calls.append(('channel', pubnub, channel))

    def uuid(self, pubnub, uuid):
        self.calls.append(('uuid', pubnub, uuid))

    def membership(self, pubnub, membership):
        self.calls.append(('membership', pubnub, membership))

    def file(self, pubnub, file_message):
        self.calls.append(('file', pubnub, file_message))


def message_on(channel, text='hello'):
    return PNMessageResult(message=text, subscription=None, channel=channel, timetoken=17000000000000000)


def app_context_event(result_class, channel):
    result = result_class(event='set', data={'id': channel})
    result.channel = channel
    result.subscription = None
    return result


def file_event(channel):
    return PNFileMessageResult(message='file', subscription=None, channel=channel, timetoken=17000000000000000,
                               publisher='user', file_url='https://example.com/f', file_id='id', file_name='f.txt')


def registry_callback(pubnub):
    callback = pubnub._subscription_registry.subscription_registry_callback
    assert callback in pubnub.listeners
    return callback


# Subscription set unsubscribe


def test_set_unsubscribe_removes_only_its_channels():
    pubnub = FakePubNub()
    registry = pubnub._subscription_registry
    pubnub.channel('ch3').subscription().subscribe()
    subscription_set = pubnub.subscription_set([
        pubnub.channel('ch1').subscription(),
        pubnub.channel('ch2').subscription()
    ])
    subscription_set.subscribe()

    subscription_set.unsubscribe()

    operation = pubnub._subscription_manager.unsubscribe_operations[-1]
    assert sorted(operation.channels) == ['ch1', 'ch2']
    assert operation.channel_groups == []
    assert registry.get_subscribed_channels() == ['ch3']
    assert subscription_set not in registry.get_all_listeners()


def test_set_unsubscribe_keeps_channel_needed_by_another_subscription():
    pubnub = FakePubNub()
    registry = pubnub._subscription_registry
    standalone = pubnub.channel('ch1').subscription()
    standalone.subscribe()
    subscription_set = pubnub.subscription_set([
        pubnub.channel('ch1').subscription(),
        pubnub.channel('ch2').subscription()
    ])
    subscription_set.subscribe()

    subscription_set.unsubscribe()

    operation = pubnub._subscription_manager.unsubscribe_operations[-1]
    assert operation.channels == ['ch2']
    assert registry.get_subscribed_channels() == ['ch1']
    assert standalone in registry.get_all_listeners()
    assert subscription_set not in registry.get_all_listeners()


def test_set_unsubscribe_with_channel_groups():
    pubnub = FakePubNub()
    registry = pubnub._subscription_registry
    subscription_set = pubnub.subscription_set([
        pubnub.channel('ch1').subscription(),
        PubNubChannelGroup(pubnub, 'group1').subscription()
    ])
    subscription_set.subscribe()

    subscription_set.unsubscribe()

    operation = pubnub._subscription_manager.unsubscribe_operations[-1]
    assert operation.channels == ['ch1']
    assert operation.channel_groups == ['group1']
    assert registry.get_subscribed_channels() == []
    assert registry.get_subscribed_channel_groups() == []


def test_unsubscribe_with_presence_removes_presence_channel():
    pubnub = FakePubNub()
    registry = pubnub._subscription_registry
    subscription = pubnub.channel('ch1').subscription(with_presence=True)
    subscription.subscribe()

    subscription.unsubscribe()

    operation = pubnub._subscription_manager.unsubscribe_operations[-1]
    assert sorted(operation.channels) == ['ch1', 'ch1-pnpres']
    assert registry.get_subscribed_channels() == []


def test_unsubscribed_channel_is_not_subscribed_again():
    pubnub = FakePubNub()
    first = pubnub.channel('ch1').subscription()
    first.subscribe()
    first.unsubscribe()

    pubnub.channel('ch2').subscription().subscribe()

    assert pubnub._subscription_manager.subscribe_operations[-1].channels == ['ch2']


def test_unsubscribe_without_changes_sends_nothing():
    pubnub = FakePubNub()
    pubnub.channel('ch1').subscription().subscribe()
    duplicate = pubnub.channel('ch1').subscription()
    duplicate.subscribe()

    duplicate.unsubscribe()

    assert pubnub._subscription_manager.unsubscribe_operations == []
    assert pubnub._subscription_registry.get_subscribed_channels() == ['ch1']


# unsubscribe_all


def test_unsubscribe_all_keeps_registry_usable():
    pubnub = FakePubNub()
    registry = pubnub._subscription_registry
    pubnub.channel('ch1').subscription().subscribe()
    PubNubChannelGroup(pubnub, 'group1').subscription().subscribe()

    registry.unsubscribe_all()

    operation = pubnub._subscription_manager.unsubscribe_operations[-1]
    assert operation.channels == ['ch1']
    assert operation.channel_groups == ['group1']
    assert registry.channels == {}
    assert registry.channel_groups == {}
    assert registry.get_subscribed_channels() == []

    pubnub.channel('ch2').subscription().subscribe()
    assert pubnub._subscription_manager.subscribe_operations[-1].channels == ['ch2']
    assert registry.get_subscribed_channels() == ['ch2']


def test_unsubscribe_all_twice_is_safe():
    pubnub = FakePubNub()
    registry = pubnub._subscription_registry
    pubnub.channel('ch1').subscription().subscribe()

    registry.unsubscribe_all()
    registry.unsubscribe_all()

    assert len(pubnub._subscription_manager.unsubscribe_operations) == 1


def test_unsubscribe_after_unsubscribe_all_does_not_raise():
    pubnub = FakePubNub()
    subscription = pubnub.channel('ch1').subscription()
    subscription.subscribe()
    pubnub._subscription_registry.unsubscribe_all()

    subscription.unsubscribe()

    assert len(pubnub._subscription_manager.unsubscribe_operations) == 1


# User metadata subscription type


def test_user_metadata_subscription_is_a_channel():
    pubnub = FakePubNub()
    subscription = PubNubUserMetadata(pubnub, 'user-1').subscription()

    assert subscription._type == PNSubscriptionType.CHANNEL

    subscription.subscribe()
    assert pubnub._subscription_registry.get_subscribed_channels() == ['user-1']
    assert pubnub._subscription_registry.get_subscribed_channel_groups() == []


# Listener dispatch


def test_app_context_and_file_events_reach_subscription_listeners():
    pubnub = FakePubNub()
    received = []
    subscription = pubnub.channel('ch1').subscription()
    subscription.on_channel_metadata = lambda event: received.append(('channel_metadata', event))
    subscription.on_user_metadata = lambda event: received.append(('user_metadata', event))
    subscription.on_membership = lambda event: received.append(('membership', event))
    subscription.on_file = lambda event: received.append(('file', event))
    subscription.subscribe()
    callback = registry_callback(pubnub)

    channel_event = app_context_event(PNChannelMetadataResult, 'ch1')
    uuid_event = app_context_event(PNUUIDMetadataResult, 'ch1')
    membership_event = app_context_event(PNMembershipResult, 'ch1')
    file_message = file_event('ch1')
    callback.channel(pubnub, channel_event)
    callback.uuid(pubnub, uuid_event)
    callback.membership(pubnub, membership_event)
    callback.file(pubnub, file_message)

    assert received == [
        ('channel_metadata', channel_event),
        ('user_metadata', uuid_event),
        ('membership', membership_event),
        ('file', file_message),
    ]


def test_app_context_events_for_other_channels_are_not_delivered():
    pubnub = FakePubNub()
    received = []
    subscription = pubnub.channel('ch1').subscription()
    subscription.on_channel_metadata = received.append
    subscription.on_file = received.append
    subscription.subscribe()
    callback = registry_callback(pubnub)

    callback.channel(pubnub, app_context_event(PNChannelMetadataResult, 'other'))
    callback.file(pubnub, file_event('other'))

    assert received == []


def test_app_context_event_without_channel_does_not_raise():
    pubnub = FakePubNub()
    received = []
    subscription = pubnub.channel('ch1').subscription()
    subscription.on_channel_metadata = received.append
    subscription.subscribe()
    callback = registry_callback(pubnub)

    callback.channel(pubnub, PNChannelMetadataResult(event='set', data={'id': 'ch1'}))

    assert received == []


def test_events_reach_subscription_set_listeners():
    pubnub = FakePubNub()
    received = []
    subscription_set = pubnub.subscription_set([
        pubnub.channel('ch1').subscription(),
        pubnub.channel('ch2').subscription()
    ])
    subscription_set.on_membership = received.append
    subscription_set.on_file = received.append
    subscription_set.subscribe()
    callback = registry_callback(pubnub)

    membership_event = app_context_event(PNMembershipResult, 'ch2')
    file_message = file_event('ch1')
    callback.membership(pubnub, membership_event)
    callback.file(pubnub, file_message)

    assert received == [membership_event, file_message]


def test_subscribe_callback_added_to_subscription_gets_pubnub_argument():
    pubnub = FakePubNub()
    listener = RecordingCallback()
    subscription = pubnub.channel('ch1').subscription()
    subscription.add_listener(listener)
    subscription.subscribe()
    callback = registry_callback(pubnub)

    message = message_on('ch1')
    channel_event = app_context_event(PNChannelMetadataResult, 'ch1')
    uuid_event = app_context_event(PNUUIDMetadataResult, 'ch1')
    membership_event = app_context_event(PNMembershipResult, 'ch1')
    file_message = file_event('ch1')
    callback.message(pubnub, message)
    callback.channel(pubnub, channel_event)
    callback.uuid(pubnub, uuid_event)
    callback.membership(pubnub, membership_event)
    callback.file(pubnub, file_message)

    assert listener.calls == [
        ('message', pubnub, message),
        ('channel', pubnub, channel_event),
        ('uuid', pubnub, uuid_event),
        ('membership', pubnub, membership_event),
        ('file', pubnub, file_message),
    ]


def test_subscription_on_message_still_gets_event_only():
    pubnub = FakePubNub()
    received = []
    subscription = pubnub.channel('ch1').subscription()
    subscription.on_message = received.append
    subscription.subscribe()
    callback = registry_callback(pubnub)

    message = message_on('ch1')
    callback.message(pubnub, message)
    callback.message(pubnub, message_on('other'))

    assert received == [message]
