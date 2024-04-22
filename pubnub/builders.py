from abc import ABCMeta, abstractmethod

from pubnub.models.subscription import PubNubChannel, PubNubChannelGroup
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
        return [PubNubChannel(self._pubnub, channel).subscription(self._presence_enabled)
                for channel in self._channel_subscriptions]

    def channel_group_subscriptions(self):
        return [PubNubChannelGroup(self._pubnub, group).subscription(self._presence_enabled)
                for group in self._channel_group_subscriptions]

    def execute(self):
        subscription = self._pubnub.subscription_set(self.channel_subscriptions() + self.channel_group_subscriptions())

        subscription.subscribe(timetoken=self._timetoken)


class UnsubscribeBuilder(PubSubBuilder):
    def execute(self):
        self._pubnub._subscription_registry.unsubscribe(channels=self._channel_subscriptions,
                                                        groups=self._channel_group_subscriptions)
