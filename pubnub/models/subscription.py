from enum import Enum
from typing import List, Optional, Union

from pubnub.callbacks import SubscribeCallback
from pubnub.dtos import SubscribeOperation, UnsubscribeOperation


class PNSubscriptionType(Enum):
    CHANNEL: str = "channel"
    CHANNEL_GROUP: str = "channel_group"


class PNSubscribable:
    pubnub = None
    subscription_names = []
    subscription_type: PNSubscriptionType = None

    def __init__(self, pubnub_instance) -> None:
        self.pubnub = pubnub_instance

    def subscription(self):
        return Subscription(self.pubnub, self.subscription_names, self.subscription_type)


class EventEmitter:
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
        else:
            return message.subscription in self.subscription_names

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


class SubscribeCapable:
    def subscribe(self, timetoken: Optional[int] = None, region: Optional[str] = None):
        self.timetoken = timetoken
        self.region = region

    def unsubscribe(self):
        pass


class Subscription(EventEmitter, SubscribeCapable):
    def __init__(self,
                 pubnub_instance,
                 subscription_names: List[str],
                 subscription_type: PNSubscriptionType) -> None:

        self.subscription_set = pubnub_instance._subscription_set
        self.subscription_manager = pubnub_instance._subscription_manager
        self.subscription = None
        self.subscription_names = subscription_names
        self.subscription_type = subscription_type
        self.with_presence = False

    def subscribe(self, timetoken: Optional[int] = None, region: Optional[str] = None, with_presence: bool = False):
        super().subscribe(timetoken, region)
        self.with_presence = with_presence
        if with_presence:
            self.subscription_names += [f'{channel}-pnpres' for channel in self.subscription_names]
        self.subscription_set.add(self)

    def unsubscribe(self):
        self.subscription_set.remove(self)

    def add_listener(self, listener):
        self.subscription_set.add_listener(listener)


class PubNubChannel(PNSubscribable):
    def __init__(self, pubnub_instance, channel_names: Union[str, List[str]]) -> None:
        super().__init__(pubnub_instance)
        self.subscription_type = PNSubscriptionType.CHANNEL
        self.subscription_names = channel_names if isinstance(channel_names, list) else [channel_names]


class PubNubChannelGroup(PNSubscribable):
    def __init__(self, pubnub_instance, channel_group_names: Union[str, List[str]]) -> None:
        super().__init__(pubnub_instance)
        self.subscription_type = PNSubscriptionType.CHANNEL_GROUP
        self.subscription_names = channel_group_names
        self.subscription_names = channel_group_names if isinstance(channel_group_names, list) \
            else [channel_group_names]


class PubNubChannelMetadata(PNSubscribable):
    def __init__(self, pubnub_instance, channel_names: Union[str, List[str]]) -> None:
        super().__init__(pubnub_instance)
        self.subscription_type = PNSubscriptionType.CHANNEL
        self.subscription_names = channel_names if isinstance(channel_names, list) else [channel_names]


class PubNubUserMetadata(PNSubscribable):
    def __init__(self, pubnub_instance, user_ids: Union[str, List[str]]) -> None:
        super().__init__(pubnub_instance)
        self.subscription_types = PNSubscriptionType.CHANNEL
        self.subscription_names = user_ids if isinstance(user_ids, list) else [user_ids]


class SubscriptionSet:
    def __init__(self, pubnub_instance):
        self.listener_set = False
        self.pubnub = pubnub_instance
        self.global_listeners = []
        self.channels = {}
        self.channel_groups = {}
        self.subscription_set_callback = None
        self.with_presence = False

    def add(self, subscription: PNSubscribable) -> list:
        if not self.subscription_set_callback:
            self.subscription_set_callback = SubscriptionSetCallback(self)
            self.pubnub.add_listener(self.subscription_set_callback)

        channel_list = []
        if subscription.subscription_type == PNSubscriptionType.CHANNEL:
            for channel in subscription.subscription_names:
                if channel not in self.channels:
                    self.channels[channel] = [subscription]
                    channel_list.append(channel)
                else:
                    self.channels[channel].append(subscription)
        else:
            for channel_group in subscription.subscription_names:
                if channel_group not in self.channel_groups:
                    self.channel_groups[channel_group] = [subscription]
                    channel_list.append(channel_group)
                else:
                    self.channel_groups[channel_group].append(subscription)

        tt = self.pubnub._subscription_manager._timetoken
        if channel_list:
            subscribe_operation = SubscribeOperation(
                channels=self.get_subscribed_channels(),
                channel_groups=self.get_subscribed_channel_groups(),
                timetoken=tt,
                presence_enabled=False
            )
            self.pubnub._subscription_manager.adapt_subscribe_builder(subscribe_operation)

        return channel_list

    def remove(self, subscription: Subscription) -> list:
        channel_list = []
        group_list = []

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
            channels=self.channels,
            channel_groups=self.channel_groups
        )
        self.pubnub._subscription_manager.adapt_unsubscribe_builder(unsubscribe_operation)
        self.channels = []
        self.channel_groups = []

    def unsubscribe(self, channels=None, groups=None):
        for channel in channels:
            del self.channels[channel]
            if self.channels[f'{channel}-pnpres']:
                del self.channels[f'{channel}-pnpres']

        for group in groups:
            del self.channel_groups[group]
            if self.channel_groups[f'{group}-pnpres']:
                del self.channel_groups[f'{group}-pnpres']

        unsubscribe_operation = UnsubscribeOperation(
            channels=channels,
            channel_groups=groups
        )
        self.pubnub._subscription_manager.adapt_unsubscribe_builder(unsubscribe_operation)


class SubscriptionSetCallback(SubscribeCallback):
    def __init__(self, subscription_set: SubscriptionSet) -> None:
        self.subscription_set = subscription_set
        super().__init__()

    def status(self, _, status):
        pass

    def presence(self, _, presence):
        for listener in self.subscription_set.get_all_listeners():
            listener.presence(presence)

    def message(self, _, message):
        for listener in self.subscription_set.get_all_listeners():
            listener.message(message)

    def signal(self, _, signal):
        for listener in self.subscription_set.get_all_listeners():
            listener.signal(signal)

    def channel(self, _, channel):
        for listener in self.subscription_set.get_all_listeners():
            listener.channel

    def uuid(self, pubnub, uuid):
        print(f'uuid: \n {uuid.__dict__}\n')

    def membership(self, _, membership):
        print(f'membership: \n {membership.__dict__}\n')

    def message_action(self, _, message_action):
        for listener in self.subscription_set.get_all_listeners():
            listener.message_action(message_action)

    def file(self, _, file_message):
        print(f'file_message: \n {file_message.__dict__}\n')
