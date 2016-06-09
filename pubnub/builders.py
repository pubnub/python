from abc import ABCMeta, abstractmethod

import six

from .dtos import SubscribeOperation, UnsubscribeOperation


class PubSubBuilder(object):
    __metaclass__ = ABCMeta

    def __init__(self, subscription_manager):
        self._subscription_manager = subscription_manager
        self._channel_subscriptions = []
        self._channel_group_subscriptions = []

    def channels(self, channels_list):
        if isinstance(channels_list, six.string_types):
            self._channel_subscriptions.append(channels_list)
        elif isinstance(channels_list, (list, dict)):
            self._channel_subscriptions.extend(channels_list)

        return self

    def channel_groups(self, channel_groups_list):
        # TODO: do the same if block as for channels
        self._channel_group_subscriptions.extend(channel_groups_list)
        return self

    @abstractmethod
    def execute(self):
        pass


class SubscribeBuilder(PubSubBuilder):
    def __init__(self, subscription_manager):
        super(SubscribeBuilder, self).__init__(subscription_manager)
        self._presence_enabled = False
        self._timetoken = 0

    def with_presence(self):
        self._presence_enabled = True
        return self

    def with_timetoken(self, timetoken):
        self._timetoken = timetoken
        return self

    def channel_subscriptions(self):
        return self._channel_subscriptions

    def channel_group_subscriptions(self):
        return self._channel_group_subscriptions

    def execute(self):
        subscribe_operation = SubscribeOperation(
            channels=self._channel_subscriptions,
            channel_groups=self._channel_group_subscriptions,
            timetoken=self._timetoken,
            presence_enabled=self._presence_enabled
        )

        self._subscription_manager.adapt_subscribe_builder(subscribe_operation)


class UnsubscribeBuilder(PubSubBuilder):
    def execute(self):
        unsubscribe_operation = UnsubscribeOperation(
            channels=self._channel_subscriptions,
            channel_groups=self._channel_group_subscriptions
        )

        self._subscription_manager.adapt_unsubscribe_builder(unsubscribe_operation)
