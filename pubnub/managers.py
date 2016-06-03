import threading

from . import utils
from .dtos import SubscribeOperation
from .models.server.subscribe import SubscribeEnvelope
from .enums import PNStatusCategory
from .callbacks import SubscribeCallback
from .models.subscription_item import SubscriptionItem
from .endpoints.pubsub.subscribe import Subscribe
from .workers import SubscribeMessageWorker
from .utils import synchronized
from .models.consumer.common import PNStatus


class PublishSequenceManager(object):
    def __init__(self, provided_max_sequence):
        self.max_sequence = provided_max_sequence
        self.next_sequence = 0

    # TODO: should be thread-safe
    def get_next_sequence(self):
        if self.max_sequence == self.next_sequence:
            self.next_sequence = 1
        else:
            self.next_sequence += 1

        return self.next_sequence


class StateManager(object):
    def __init__(self):
        self._channels = {}
        self._groups = {}
        self._presence_channels = {}
        self._presence_groups = {}

    def prepare_channel_list(self, include_presence):
        return StateManager._prepare_membership_list(
            self._channels, self._presence_channels, include_presence)

    def prepare_channel_group_list(self, include_presence):
        return StateManager._prepare_membership_list(
            self._channels, self._presence_channels, include_presence)

    def adapt_subscribe_builder(self, subscribe_operation):
        for channel in subscribe_operation.channels:
            self._channels[channel] = SubscriptionItem(name=channel)

            if subscribe_operation.presence_enabled:
                self._presence_channels[channel] = SubscriptionItem(name=channel)

        for group in subscribe_operation.channel_groups:
            self._groups[group] = SubscriptionItem(name=group)

            if subscribe_operation.presence_enabled:
                self._presence_groups[group] = SubscriptionItem(name=group)

    @staticmethod
    def _prepare_membership_list(data_storage, presence_storage, include_presence):
        response = []

        for item in data_storage.values():
            response.append(item.name)

        if include_presence:
            for item in presence_storage.values():
                response.append(item.name + "-pnpres")

        return response


class ListenerManager(object):
    def __init__(self, pubnub_instance):
        self._pubnub = pubnub_instance
        self._listeners = []

    def add_listener(self, listener):
        assert isinstance(listener, SubscribeCallback)
        self._listeners.append(listener)

    def remove_listener(self, listener):
        assert isinstance(listener, SubscribeCallback)
        self._listeners.remove(listener)

    def announce_status(self, status):
        for callback in self._listeners:
            callback.status(self._pubnub, status)

    def announce_message(self, message):
        for callback in self._listeners:
            callback.message(self._pubnub, message)

    def announce_presence(self, presence):
        for callback in self._listeners:
            callback.presence(self._pubnub, presence)


class SubscriptionManager(object):
    def __init__(self, pubnub_instance):
        self._pubnub = pubnub_instance
        self._subscription_status_announced = False
        # TODO: ensure this is a correct Queue
        self._message_queue = utils.Queue()
        self._subscription_state = StateManager()
        self._listener_manager = ListenerManager(self._pubnub)
        self._timetoken = int(0)
        self._region = None

        self._should_stop = False

        self._subscribe_call = None
        self._heartbeat_call = None

        self._consumer_event = threading.Event()
        consumer = SubscribeMessageWorker(self._pubnub, self._listener_manager,
                                          self._message_queue, self._consumer_event)
        self._consumer_thread = threading.Thread(target=consumer.run,
                                                 name="SubscribeMessageWorker")
        self._consumer_thread.start()

    def add_listener(self, listener):
        self._listener_manager.add_listener(listener)

    @synchronized
    def adapt_subscribe_builder(self, subscribe_operation):
        assert isinstance(subscribe_operation, SubscribeOperation)
        self._subscription_state.adapt_subscribe_builder(subscribe_operation)
        self._subscription_status_announced = False

        if subscribe_operation.timetoken is not None:
            self._timetoken = subscribe_operation.timetoken

        self.reconnect()

    @synchronized
    def reconnect(self):
        self._should_stop = False
        self._start_subscribe_loop()
        self._register_heartbeat_timer()

    def stop(self):
        # self._stop_heartbeat_timer()
        self._stop_subscribe_loop()
        self._should_stop = True
        self._consumer_event.set()

    def _start_subscribe_loop(self):
        self._stop_subscribe_loop()

        combined_channels = self._subscription_state.prepare_channel_list(True)
        combined_groups = self._subscription_state.prepare_channel_group_list(True)

        if len(combined_channels) == 0 and len(combined_groups) == 0:
            return

        def callback(raw_result, status):
            """ SubscribeEndpoint callback"""
            assert isinstance(status, PNStatus)

            if status.is_error():
                if status.category is PNStatusCategory.PNTimeoutCategory and not self._should_stop:
                    self._start_subscribe_loop()
                else:
                    self._listener_manager.announce_status(status)

                return

            if not self._subscription_status_announced:
                pn_status = PNStatus()
                pn_status.category = PNStatusCategory.PNConnectedCategory,
                pn_status.status_code = status.status_code
                pn_status.auth_key = status.auth_key
                pn_status.operation = status.operation
                pn_status.client_request = status.client_request
                pn_status.origin = status.origin
                pn_status.tls_enabled = status.tls_enabled

                self._subscription_status_announced = True
                self._listener_manager.announce_status(pn_status)

            result = SubscribeEnvelope.from_json(raw_result)
            if result.messages is not None and len(result.messages) > 0:
                for message in result.messages:
                    self._message_queue.put(message)

            # REVIEW: is int compatible with long for Python 2
            self._timetoken = int(result.metadata.timetoken)
            self._region = int(result.metadata.region)
            self._start_subscribe_loop()

        try:
            self._subscribe_call = Subscribe(self._pubnub) \
                .channels(combined_channels).groups(combined_groups) \
                .timetoken(self._timetoken).region(self._region) \
                .filter_expression(self._pubnub.config.filter_expression) \
                .async(callback)
        except Exception as e:
            print("failed", e)

    def _stop_subscribe_loop(self):
        sc = self._subscribe_call

        if sc is not None and not sc.is_executed and not sc.is_canceled:
            sc.cancel()

    # TODO: implement
    def _stop_heartbeat_timer(self):
        pass

    # TODO: implement
    def _register_heartbeat_timer(self):
        pass
