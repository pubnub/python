from abc import ABCMeta, abstractmethod
from . import utils


class PubSubBuilder(object):
    __metaclass__ = ABCMeta

    def __init__(self, pubnub_instance):
        self._pubnub = pubnub_instance
        self._channel_subscriptions = []
        self._channel_group_subscriptions = []

    # TODO: make the 'channel' alias
    def channels(self, channels_list):
        utils.extend_list(self._channel_subscriptions, channels_list)

        return self

    def channel_groups(self, channel_groups_list):
        utils.extend_list(self._channel_group_subscriptions, channel_groups_list)

        return self

    @abstractmethod
    def execute(self):
        pass


class SubscribeBuilder(PubSubBuilder):
    def __init__(self, pubnub_instance):
        super(SubscribeBuilder, self).__init__(pubnub_instance)
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
        if self._channel_subscriptions:
            channels_subscription = self._pubnub.channel(self._channel_subscriptions).subscription()
            channels_subscription.subscribe(with_presence=self._presence_enabled, timetoken=self._timetoken)
        if self._channel_group_subscriptions:
            groups_subscription = self._pubnub.channel_group(self._channel_group_subscriptions).subscription()
            groups_subscription.subscribe(with_presence=self._presence_enabled, timetoken=self._timetoken)


class UnsubscribeBuilder(PubSubBuilder):
    def execute(self):
        self._pubnub._subscription_registry.unsubscribe(channels=self._channel_subscriptions,
                                                        groups=self._channel_group_subscriptions)
