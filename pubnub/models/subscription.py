from enum import Enum
from typing import List, Optional, Union

from pubnub.callbacks import SubscribeCallback
from pubnub.dtos import SubscribeOperation, UnsubscribeOperation


class PNSubscriptionType(Enum):
    CHANNEL: str = "channel"
    CHANNEL_GROUP: str = "channel_group"


class PNSubscribable:
    pubnub = None
    name: str
    _type: PNSubscriptionType = None

    def __init__(self, pubnub_instance, name) -> None:
        self.pubnub = pubnub_instance
        self.name = name

    def subscription(self, with_presence: bool = None):
        return PubNubSubscription(self.pubnub, self.name, self._type, with_presence=with_presence)


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
        if isinstance(self, PubNubSubscriptionSet):
            return any([subscription_item.is_matching_listener(message)
                        for subscription_item in self.get_subscription_items()])
        else:
            if self._type == PNSubscriptionType.CHANNEL:
                return message.channel == self.name or wildcard_match(message.channel, self.name)
            else:
                return message.subscription == self.name

    def presence(self, presence):
        if not hasattr(self, 'on_presence') or not (hasattr(self, 'with_presence') and self.with_presence):
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
    def subscribe(self, timetoken: Optional[int] = None, region: Optional[str] = None):
        self.timetoken = timetoken
        self.region = region
        self.subscription_registry.add(self)

    def unsubscribe(self):
        self.subscription_registry.remove(self)


class PubNubSubscription(PNEventEmitter, PNSubscribeCapable):
    def __init__(self, pubnub_instance, name: str, type: PNSubscriptionType, with_presence: bool = False) -> None:
        self.subscription_registry = pubnub_instance._subscription_registry
        self.subscription_manager = pubnub_instance._subscription_manager
        self.name = name
        self._type = type
        self.with_presence = with_presence

    def add_listener(self, listener):
        self.subscription_registry.add_listener(listener)

    def get_names_with_presence(self):
        return [self.name, f'{self.name}-pnpres'] if self.with_presence else [self.name]


class PubNubSubscriptionSet(PNEventEmitter, PNSubscribeCapable):
    def __init__(self, pubnub_instance, subscriptions: List[PubNubSubscription]) -> None:
        self.subscription_registry = pubnub_instance._subscription_registry
        self.subscription_manager = pubnub_instance._subscription_manager
        self.subscriptions = subscriptions

    def get_subscription_items(self):
        return [item for item in self.subscriptions]


class PubNubChannel(PNSubscribable):
    _type = PNSubscriptionType.CHANNEL

    def __init__(self, pubnub_instance, channel: str) -> None:
        super().__init__(pubnub_instance, channel)


class PubNubChannelGroup(PNSubscribable):
    _type = PNSubscriptionType.CHANNEL_GROUP

    def __init__(self, pubnub_instance, channel_group: str) -> None:
        super().__init__(pubnub_instance, channel_group)


class PubNubChannelMetadata(PNSubscribable):
    _type = PNSubscriptionType.CHANNEL

    def __init__(self, pubnub_instance, channel: str) -> None:
        super().__init__(pubnub_instance, channel)


class PubNubUserMetadata(PNSubscribable):
    _types = PNSubscriptionType.CHANNEL

    def __init__(self, pubnub_instance, user_id: str) -> None:
        super().__init__(pubnub_instance, user_id)


class PNSubscriptionRegistry:
    def __init__(self, pubnub_instance):
        self.pubnub = pubnub_instance
        self.global_listeners = []
        self.channels = {}
        self.channel_groups = {}
        self.subscription_registry_callback = None
        self.with_presence = None
        self.subscriptions = []

    def __add_subscription(self, subscription: PubNubSubscription, subscription_set: PubNubSubscriptionSet = None):
        names_added = []
        self.subscriptions.append(subscription)

        subscriptions = [subscription]
        if subscription_set:
            subscriptions.append(subscription_set)

        if subscription._type == PNSubscriptionType.CHANNEL:
            subscription_list = self.channels
        else:
            subscription_list = self.channel_groups

        for name in subscription.get_names_with_presence():
            if name not in subscription_list:
                subscription_list[name] = subscriptions
                names_added.append(name)
            else:
                subscription_list[name].extend(subscriptions)
        return names_added

    def __remove_subscription(self, subscription: PubNubSubscription):
        names_removed = {'channels': [],
                         'groups': []}

        self.subscriptions.remove(subscription)

        if subscription._type == PNSubscriptionType.CHANNEL:
            subscription_list = self.channels
            removed = names_removed['channels']
        else:
            subscription_list = self.channel_groups
            removed = names_removed['groups']

        for name in subscription.get_names_with_presence():
            if name in subscription_list and subscription in subscription_list[name]:
                subscription_list[name].remove(subscription)
                if len(subscription_list[name]) == 0:
                    removed.append(name)

        return names_removed

    def add(self, subscription: Union[PubNubSubscription, PubNubSubscriptionSet]) -> list:
        if not self.subscription_registry_callback:
            self.subscription_registry_callback = PNSubscriptionRegistryCallback(self)
            self.pubnub.add_listener(self.subscription_registry_callback)

        self.with_presence = any(sub.with_presence for sub in self.subscriptions)

        names_changed = []
        if isinstance(subscription, PubNubSubscriptionSet):
            for subscription_part in subscription.subscriptions:
                names_changed.append(self.__add_subscription(subscription_part, subscription))
        else:
            names_changed.append(self.__add_subscription(subscription))

        tt = self.pubnub._subscription_manager._timetoken
        if subscription.timetoken:
            tt = max(subscription.timetoken, self.pubnub._subscription_manager._timetoken)

        if names_changed:
            subscribe_operation = SubscribeOperation(
                channels=self.get_subscribed_channels(),
                channel_groups=self.get_subscribed_channel_groups(),
                timetoken=tt,
                presence_enabled=self.with_presence,
            )
            self.pubnub._subscription_manager.adapt_subscribe_builder(subscribe_operation)
        return names_changed

    def remove(self, subscription: Union[PubNubSubscription, PubNubSubscriptionSet]) -> list:
        channels_changed = []
        groups_changed = []

        if isinstance(subscription, PubNubSubscriptionSet):
            for subscription_part in subscription.subscriptions:
                names_changed = self.__remove_subscription(subscription_part)
                channels_changed += names_changed['channels']
                groups_changed += names_changed['groups']
        else:
            names_changed = self.__remove_subscription(subscription)
            channels_changed += names_changed['channels']
            groups_changed += names_changed['groups']

        self.with_presence = any(sub.with_presence for sub in self.subscriptions)

        if names_changed:
            unsubscribe_operation = UnsubscribeOperation(channels=channels_changed, channel_groups=groups_changed)
            self.pubnub._subscription_manager.adapt_unsubscribe_builder(unsubscribe_operation)
        return names_changed

    def get_subscribed_channels(self):
        return list(self.channels.keys())

    def get_subscribed_channel_groups(self):
        return list(self.channel_groups.keys())

    def get_subscriptions_for(self, _type: PNSubscriptionType, name: str):
        if _type == PNSubscriptionType.CHANNEL:
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
        presence_channels = []
        for channel in channels:
            del self.channels[channel]
            if f'{channel}-pnpres' in self.channels:
                del self.channels[f'{channel}-pnpres']
                presence_channels.append(f'{channel}-pnpres')

        presence_groups = []
        for group in groups:
            del self.channel_groups[group]
            if f'{group}-pnpres' in self.channel_groups:
                del self.channel_groups[f'{group}-pnpres']
                presence_groups.append(f'{group}-pnpres')

        unsubscribe_operation = UnsubscribeOperation(
            channels=channels + presence_channels,
            channel_groups=groups + presence_groups
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
            listener.channel(channel)

    def uuid(self, pubnub, uuid):
        for listener in self.subscription_registry.get_all_listeners():
            listener.uuid(uuid)

    def membership(self, _, membership):
        for listener in self.subscription_registry.get_all_listeners():
            listener.membership(membership)

    def message_action(self, _, message_action):
        for listener in self.subscription_registry.get_all_listeners():
            listener.message_action(message_action)

    def file(self, _, file_message):
        for listener in self.subscription_registry.get_all_listeners():
            listener.file_message(file_message)
