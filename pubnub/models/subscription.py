from enum import Enum
from typing import List, Optional, Union

from pubnub.callbacks import SubscribeCallback
from pubnub.dtos import SubscribeOperation, UnsubscribeOperation


class PNSubscriptionType(Enum):
    CHANNEL: str = "channel"
    CHANNEL_GROUP: str = "channel_group"
    SUBSCRIPTION_SET: str = "subscription_set"


class PNSubscribable:
    pubnub = None
    subscription_names = []
    subscription_type: PNSubscriptionType = None

    def __init__(self, pubnub_instance) -> None:
        self.pubnub = pubnub_instance

    def subscription(self, *, timetoken: Optional[int] = None, region: Optional[str] = None,
                     with_presence: Optional[bool] = None):
        return PubNubSubscription(self.pubnub, self.subscription_names, self.subscription_type, timetoken, region,
                                  with_presence)


class PNEventEmitter:
    on_message: callable
    on_signal: callable
    on_presence: callable
    on_channel_metadata: callable
    on_user_metadata: callable
    on_message_action: callable
    on_membership: callable
    on_file: callable

    def is_matching_listener(self, message):
        def wildcard_match(name, subscription):
            return subscription.endswith('.*') and name.startswith(subscription.strip('*'))

        if self.subscription_type == PNSubscriptionType.CHANNEL:
            return any(
                [message.channel == subscription or wildcard_match(message.channel, subscription)
                    for subscription in self.subscription_names]
            )
        elif self.subscription_type == PNSubscriptionType.CHANNEL_GROUP:
            return message.subscription in self.subscription_names
        else:
            return any(
                [message.channel == subscription or wildcard_match(message.channel, subscription)
                    for subscription in (self.channels + self.channel_groups)]
            )

    def presence(self, presence):
        if not hasattr(self, 'on_presence') or not self.with_presence:
            return

        if self.is_matching_listener(presence) and hasattr(self, 'on_presence'):
            self.on_presence(presence)

    def message(self, message):
        if self.is_matching_listener(message) and hasattr(self, 'on_message'):
            self.on_message(message)

    def message_action(self, message_action):
        if self.is_matching_listener(message_action) and hasattr(self, 'on_message_action'):
            self.on_message_action(message_action)

    def signal(self, signal):
        if self.is_matching_listener(signal) and hasattr(self, 'on_signal'):
            self.on_signal(signal)


class PNSubscribeCapable:
    def subscribe(self):
        self.subscription_registry.add(self)

    def unsubscribe(self):
        self.subscription_registry.remove(self)


class PubNubSubscription(PNEventEmitter, PNSubscribeCapable):
    def __init__(self, pubnub_instance,
                 subscription_names: List[str],
                 subscription_type: PNSubscriptionType,
                 timetoken: Optional[int] = None,
                 region: Optional[str] = None,
                 with_presence: bool = False) -> None:

        self.subscription_registry = pubnub_instance._subscription_registry
        self.subscription_manager = pubnub_instance._subscription_manager
        self.subscription = None
        self.subscription_names = subscription_names
        self.subscription_type = subscription_type
        self.timetoken = timetoken
        self.region = region
        self.with_presence = with_presence

    def add_listener(self, listener):
        self.subscription_registry.add_listener(listener)


class PubNubSubscriptionSet(PNEventEmitter, PNSubscribeCapable):
    def __init__(self, pubnub_instance,
                 channels: Optional[List[str]] = None,
                 channel_groups: Optional[List[str]] = None,
                 timetoken: Optional[int] = None,
                 region: Optional[str] = None,
                 with_presence: Optional[bool] = None) -> None:
        self.subscription_type = PNSubscriptionType.SUBSCRIPTION_SET
        self.subscription_registry = pubnub_instance._subscription_registry
        self.subscription_manager = pubnub_instance._subscription_manager
        self.channels = channels
        self.channel_groups = channel_groups
        self.timetoken = timetoken
        self.region = region
        self.with_presence = with_presence


class PubNubChannel(PNSubscribable):
    def __init__(self, pubnub_instance, channel: Union[str, List[str]]) -> None:
        super().__init__(pubnub_instance)
        self.subscription_type = PNSubscriptionType.CHANNEL
        self.subscription_names = channel if isinstance(channel, list) else [channel]


class PubNubChannelGroup(PNSubscribable):
    def __init__(self, pubnub_instance, channel_group: Union[str, List[str]]) -> None:
        super().__init__(pubnub_instance)
        self.subscription_type = PNSubscriptionType.CHANNEL_GROUP
        self.subscription_names = channel_group
        self.subscription_names = channel_group if isinstance(channel_group, list) \
            else [channel_group]


class PubNubChannelMetadata(PNSubscribable):
    def __init__(self, pubnub_instance, channel: Union[str, List[str]]) -> None:
        super().__init__(pubnub_instance)
        self.subscription_type = PNSubscriptionType.CHANNEL
        self.subscription_names = channel if isinstance(channel, list) else [channel]


class PubNubUserMetadata(PNSubscribable):
    def __init__(self, pubnub_instance, user_id: Union[str, List[str]]) -> None:
        super().__init__(pubnub_instance)
        self.subscription_types = PNSubscriptionType.CHANNEL
        self.subscription_names = user_id if isinstance(user_id, list) else [user_id]


class PNSubscriptionRegistry:
    def __init__(self, pubnub_instance):
        self.listener_set = False
        self.pubnub = pubnub_instance
        self.global_listeners = []
        self.channels = {}
        self.channel_groups = {}
        self.subscription_registry_callback = None
        self.with_presence = None
        self.subscriptions = []

    def add(self, subscription: PNSubscribable) -> list:
        if not self.subscription_registry_callback:
            self.subscription_registry_callback = PNSubscriptionRegistryCallback(self)
            self.pubnub.add_listener(self.subscription_registry_callback)

        self.subscriptions.append(subscription)
        self.with_presence = any(sub.with_presence for sub in self.subscriptions)

        channel_list = []
        if isinstance(subscription, PubNubSubscriptionSet):
            for channel in subscription.channels:
                if channel not in self.channels:
                    self.channels[channel] = [subscription]
                    channel_list.append(channel)
                else:
                    self.channels[channel].append(subscription)
            for channel_group in subscription.channel_groups:
                if channel_group not in self.channel_groups:
                    self.channel_groups[channel_group] = [subscription]
                    channel_list.append(channel_group)
                else:
                    self.channel_groups[channel_group].append(subscription)
        elif subscription.subscription_type == PNSubscriptionType.CHANNEL:
            for channel in subscription.subscription_names:
                if channel not in self.channels:
                    self.channels[channel] = [subscription]
                    channel_list.append(channel)
                else:
                    self.channels[channel].append(subscription)
        elif subscription.subscription_type == PNSubscriptionType.CHANNEL_GROUP:
            for channel_group in subscription.subscription_names:
                if channel_group not in self.channel_groups:
                    self.channel_groups[channel_group] = [subscription]
                    channel_list.append(channel_group)
                else:
                    self.channel_groups[channel_group].append(subscription)
        else:
            raise NotImplementedError('Unknown Subscription type')

        tt = self.pubnub._subscription_manager._timetoken
        if subscription.timetoken:
            tt = max(subscription.timetoken, self.pubnub._subscription_manager._timetoken)

        if channel_list:
            subscribe_operation = SubscribeOperation(
                channels=self.get_subscribed_channels(),
                channel_groups=self.get_subscribed_channel_groups(),
                timetoken=tt,
                presence_enabled=self.with_presence,
            )
            self.pubnub._subscription_manager.adapt_subscribe_builder(subscribe_operation)

        return channel_list

    def remove(self, subscription: PubNubSubscription) -> list:
        channel_list = []
        group_list = []
        self.subscriptions.remove(subscription)
        self.with_presence = any(sub.with_presence for sub in self.subscriptions)

        if subscription.subscription_type == PNSubscriptionType.CHANNEL:
            for channel in subscription.subscription_names:
                if channel in self.channels:
                    self.channels[channel].remove(subscription)
                    if self.channels[channel] == []:
                        del self.channels[channel]
                        channel_list.append(channel)
        else:
            for channel_group in subscription.subscription_names:
                if channel_group in self.channel_groups:
                    self.channel_groups[channel_group].remove(subscription)
                if not self.channel_groups[channel_group]:
                    del self.channel_groups[channel_group]
                    group_list.append(channel_group)

        if channel_list:
            unsubscribe_operation = UnsubscribeOperation(
                channels=channel_list,
                channel_groups=group_list
            )
            self.pubnub._subscription_manager.adapt_unsubscribe_builder(unsubscribe_operation)
        return channel_list

    def get_subscribed_channels(self):
        return list(self.channels.keys())

    def get_subscribed_channel_groups(self):
        return list(self.channel_groups.keys())

    def get_subscriptions_for(self, subscription_type: PNSubscriptionType, name: str):
        if subscription_type == PNSubscriptionType.CHANNEL:
            return [channel for channel in self.get_subscribed_channels() if channel == name]
        else:
            return [group for group in self.get_subscribed_channel_groups() if group == name]

    def get_all_listeners(self):
        listeners = []

        for channel in self.channels:
            listeners += self.channels[channel]
        for channel_group in self.channel_groups:
            listeners += self.channel_groups[channel_group]
        if self.global_listeners:
            listeners += self.global_listeners
        return set(listeners)

    def add_listener(self, listener):
        assert isinstance(listener, SubscribeCallback)
        self.global_listeners.append(listener)

    def remove_listener(self, listener):
        assert isinstance(listener, SubscribeCallback)
        self.global_listeners.remove(listener)

    def unsubscribe_all(self):
        unsubscribe_operation = UnsubscribeOperation(
            channels=list(self.channels.keys()),
            channel_groups=list(self.channel_groups.keys())
        )
        self.pubnub._subscription_manager.adapt_unsubscribe_builder(unsubscribe_operation)
        self.channels = []
        self.channel_groups = []

    def unsubscribe(self, channels=None, groups=None):
        for channel in channels:
            del self.channels[channel]
            if f'{channel}-pnpres' in self.channels:
                del self.channels[f'{channel}-pnpres']

        for group in groups:
            del self.channel_groups[group]
            if f'{group}-pnpres' in self.channel_groups:
                del self.channel_groups[f'{group}-pnpres']

        unsubscribe_operation = UnsubscribeOperation(
            channels=channels,
            channel_groups=groups
        )
        self.pubnub._subscription_manager.adapt_unsubscribe_builder(unsubscribe_operation)


class PNSubscriptionRegistryCallback(SubscribeCallback):
    def __init__(self, subscription_registry: PNSubscriptionRegistry) -> None:
        self.subscription_registry = subscription_registry
        super().__init__()

    def status(self, _, status):
        pass

    def presence(self, _, presence):
        for listener in self.subscription_registry.get_all_listeners():
            listener.presence(presence)

    def message(self, _, message):
        for listener in self.subscription_registry.get_all_listeners():
            listener.message(message)

    def signal(self, _, signal):
        for listener in self.subscription_registry.get_all_listeners():
            listener.signal(signal)

    def channel(self, _, channel):
        for listener in self.subscription_registry.get_all_listeners():
            listener.channel

    def uuid(self, pubnub, uuid):
        print(f'uuid: \n {uuid.__dict__}\n')

    def membership(self, _, membership):
        print(f'membership: \n {membership.__dict__}\n')

    def message_action(self, _, message_action):
        for listener in self.subscription_registry.get_all_listeners():
            listener.message_action(message_action)

    def file(self, _, file_message):
        print(f'file_message: \n {file_message.__dict__}\n')
