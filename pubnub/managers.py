import logging
from abc import abstractmethod, ABCMeta

import math
import time
import copy
import base64
from cbor2 import loads

from . import utils
from .enums import PNStatusCategory, PNReconnectionPolicy, PNOperationType, PNResourceType, PNMatchType
from .models.consumer.common import PNStatus
from .models.server.subscribe import SubscribeEnvelope
from .dtos import SubscribeOperation, UnsubscribeOperation
from .callbacks import SubscribeCallback, ReconnectionCallback
from .models.subscription_item import SubscriptionItem
from .errors import PNERR_INVALID_ACCESS_TOKEN
from .exceptions import PubNubException

logger = logging.getLogger("pubnub")


class PublishSequenceManager(object):
    def __init__(self, provided_max_sequence):
        self.max_sequence = provided_max_sequence
        self.next_sequence = 0

    @abstractmethod
    def get_next_sequence(self):
        if self.max_sequence == self.next_sequence:
            self.next_sequence = 1
        else:
            self.next_sequence += 1
        return self.next_sequence


class BasePathManager(object):
    MAX_SUBDOMAIN = 20
    DEFAULT_SUBDOMAIN = "pubsub"
    DEFAULT_BASE_PATH = "pubnub.com"

    def __init__(self, initial_config):
        self.config = initial_config
        self._current_subdomain = 1

    def get_base_path(self):
        if self.config.origin is not None:
            return self.config.origin
        # TODO: should CacheBusting be used?
        elif False:
            constructed_url = ("ps%s.%s" % (self._current_subdomain, BasePathManager.DEFAULT_BASE_PATH))

            if self._current_subdomain == BasePathManager.MAX_SUBDOMAIN:
                self._current_subdomain = 1
            else:
                self._current_subdomain += 1

            return constructed_url
        else:
            return "%s.%s" % (BasePathManager.DEFAULT_SUBDOMAIN, BasePathManager.DEFAULT_BASE_PATH)


class ReconnectionManager(object):
    INTERVAL = 3
    MINEXPONENTIALBACKOFF = 1
    MAXEXPONENTIALBACKOFF = 32

    def __init__(self, pubnub):
        self._pubnub = pubnub
        self._callback = None
        self._timer = None
        self._timer_interval = None
        self._connection_errors = 1

    def set_reconnection_listener(self, reconnection_callback):
        assert isinstance(reconnection_callback, ReconnectionCallback)
        self._callback = reconnection_callback

    def _recalculate_interval(self):
        if self._pubnub.config.reconnect_policy == PNReconnectionPolicy.EXPONENTIAL:
            self._timer_interval = int(math.pow(2, self._connection_errors) - 1)
            if self._timer_interval > self.MAXEXPONENTIALBACKOFF:
                self._timer_interval = self.MINEXPONENTIALBACKOFF
                self._connection_errors = 1
                logger.debug("timerInterval > MAXEXPONENTIALBACKOFF at: %s" % utils.datetime_now())
            elif self._timer_interval < 1:
                self._timer_interval = self.MINEXPONENTIALBACKOFF
            logger.debug("timerInterval = %d at: %s" % (self._timer_interval, utils.datetime_now()))
        else:
            self._timer_interval = self.INTERVAL

    @abstractmethod
    def start_polling(self):
        pass

    def _stop_heartbeat_timer(self):
        if self._timer is not None:
            self._timer.stop()
            self._timer = None


class StateManager(object):
    def __init__(self):
        self._channels = {}
        self._groups = {}
        self._presence_channels = {}
        self._presence_groups = {}

    def is_empty(self):
        return len(self._channels) == 0 and len(self._groups) == 0 and\
            len(self._presence_channels) == 0 and len(self._presence_groups) == 0

    def subscribed_to_the_only_channel(self):
        return len(self._channels) == 1 and len(self._groups) == 0 and\
            len(self._presence_channels) == 0 and len(self._presence_groups) == 0

    def prepare_channel_list(self, include_presence):
        return StateManager._prepare_membership_list(
            self._channels, self._presence_channels, include_presence)

    def prepare_channel_group_list(self, include_presence):
        return StateManager._prepare_membership_list(
            self._groups, self._presence_groups, include_presence)

    def adapt_subscribe_builder(self, subscribe_operation):
        for channel in subscribe_operation.channels:
            self._channels[channel] = SubscriptionItem(name=channel)

            if subscribe_operation.presence_enabled:
                self._presence_channels[channel] = SubscriptionItem(name=channel)

        for group in subscribe_operation.channel_groups:
            self._groups[group] = SubscriptionItem(name=group)

            if subscribe_operation.presence_enabled:
                self._presence_groups[group] = SubscriptionItem(name=group)

    def adapt_unsubscribe_builder(self, unsubscribe_operation):
        for channel in unsubscribe_operation.channels:
            self._channels.pop(channel, None)
            if channel in self._presence_channels:
                self._presence_channels.pop(channel, None)

        for group in unsubscribe_operation.channel_groups:
            self._groups.pop(group)
            if group in self._presence_groups:
                self._presence_groups.pop(group)

    def adapt_state_builder(self, state_operation):
        for channel in state_operation.channels:
            subscribed_channel = self._channels.get(channel)

            if subscribed_channel is not None:
                subscribed_channel.state = state_operation.state

        for group in state_operation.channel_groups:
            subscribed_group = self._channels.get(group)

            if subscribed_group is not None:
                subscribed_group.state = state_operation.state

    def state_payload(self):
        state = {}

        for channel in self._channels.values():
            if channel.state is not None:
                state[channel.name] = channel.state

        for group in self._groups.values():
            if group.state is not None:
                state[group.name] = group.state

        return state

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

    def announce_signal(self, signal):
        for callback in self._listeners:
            callback.signal(self._pubnub, signal)

    def announce_channel(self, channel):
        for callback in self._listeners:
            callback.channel(self._pubnub, channel)

    def announce_uuid(self, uuid):
        for callback in self._listeners:
            callback.uuid(self._pubnub, uuid)

    def announce_membership(self, membership):
        for callback in self._listeners:
            callback.membership(self._pubnub, membership)

    def announce_message_action(self, message_action):
        for callback in self._listeners:
            callback.message_action(self._pubnub, message_action)

    def announce_presence(self, presence):
        for callback in self._listeners:
            callback.presence(self._pubnub, presence)

    def announce_file_message(self, file_message):
        for callback in self._listeners:
            callback.file(self._pubnub, file_message)


class SubscriptionManager(object):
    __metaclass__ = ABCMeta

    HEARTBEAT_INTERVAL_MULTIPLIER = 1000

    def __init__(self, pubnub_instance):
        self._pubnub = pubnub_instance
        self._subscription_status_announced = False

        self._subscription_state = StateManager()
        self._listener_manager = ListenerManager(self._pubnub)
        self._timetoken = 0
        self._region = None

        self._should_stop = False

        self._subscribe_request_task = None
        self._heartbeat_call = None

    @abstractmethod
    def _start_worker(self):
        pass

    @abstractmethod
    def _set_consumer_event(self):
        pass

    @abstractmethod
    def _message_queue_put(self, message):
        pass

    @abstractmethod
    def _start_subscribe_loop(self):
        pass

    @abstractmethod
    def _stop_subscribe_loop(self):
        pass

    @abstractmethod
    def _stop_heartbeat_timer(self):
        pass

    @abstractmethod
    def _perform_heartbeat_loop(self):
        pass

    @abstractmethod
    def _send_leave(self, unsubscribe_operation):
        pass

    def add_listener(self, listener):
        self._listener_manager.add_listener(listener)

    def remove_listener(self, listener):
        self._listener_manager.remove_listener(listener)

    def get_subscribed_channels(self):
        return self._subscription_state.prepare_channel_list(False)

    def get_subscribed_channel_groups(self):
        return self._subscription_state.prepare_channel_group_list(False)

    def unsubscribe_all(self):
        self.adapt_unsubscribe_builder(UnsubscribeOperation(
            channels=self._subscription_state.prepare_channel_list(False),
            channel_groups=self._subscription_state.prepare_channel_group_list(False)
        ))

    def adapt_subscribe_builder(self, subscribe_operation):
        assert isinstance(subscribe_operation, SubscribeOperation)
        self._subscription_state.adapt_subscribe_builder(subscribe_operation)
        self._subscription_status_announced = False

        if subscribe_operation.timetoken is not None:
            self._timetoken = subscribe_operation.timetoken

        self.reconnect()

    def adapt_unsubscribe_builder(self, unsubscribe_operation):
        assert isinstance(unsubscribe_operation, UnsubscribeOperation)

        self._subscription_state.adapt_unsubscribe_builder(unsubscribe_operation)

        if not self._pubnub.config.suppress_leave_events:
            self._send_leave(unsubscribe_operation)

        if self._subscription_state.is_empty():
            self._region = None
            self._timetoken = 0
        self.reconnect()

    def adapt_state_builder(self, state_operation):
        self._subscription_state.adapt_state_builder(state_operation)
        self.reconnect()

    @abstractmethod
    def reconnect(self):
        pass

    def stop(self):
        self._should_stop = True
        self._stop_subscribe_loop()
        self._stop_heartbeat_timer()
        self._set_consumer_event()

    def _handle_endpoint_call(self, raw_result, status):
        assert isinstance(status, PNStatus)

        if not self._subscription_status_announced:
            pn_status = PNStatus()
            pn_status.category = PNStatusCategory.PNConnectedCategory
            pn_status.status_code = status.status_code
            pn_status.auth_key = status.auth_key
            pn_status.operation = status.operation
            pn_status.client_request = status.client_request
            pn_status.origin = status.origin
            pn_status.tls_enabled = status.tls_enabled
            pn_status.affected_channels = status.affected_channels
            pn_status.affected_groups = status.affected_groups

            self._subscription_status_announced = True
            self._listener_manager.announce_status(pn_status)

        result = SubscribeEnvelope.from_json(raw_result)
        only_channel = self._subscription_state.subscribed_to_the_only_channel()
        if result.messages is not None and len(result.messages) > 0:
            for message in result.messages:
                if only_channel:
                    message.only_channel_subscription = True
                self._message_queue_put(message)

        # REVIEW: is int compatible with long for Python 2
        self._timetoken = int(result.metadata.timetoken)
        self._region = int(result.metadata.region)

    # TODO: make abstract
    def _register_heartbeat_timer(self):
        self._stop_heartbeat_timer()


class TelemetryManager(object):  # pylint: disable=W0612
    TIMESTAMP_DIVIDER = 1000
    MAXIMUM_LATENCY_DATA_AGE = 60
    CLEAN_UP_INTERVAL = 1
    CLEAN_UP_INTERVAL_MULTIPLIER = 1000

    def __init__(self):
        self.latencies = {}

    @abstractmethod
    def _start_clean_up_timer(self):
        pass

    @abstractmethod
    def _stop_clean_up_timer(self):
        pass

    def operation_latencies(self):
        operation_latencies = {}

        for endpoint_name, endpoint_latencies in self.latencies.items():
            latency_key = 'l_' + endpoint_name

            endpoint_average_latency = self.average_latency_from_data(endpoint_latencies)

            if endpoint_average_latency > 0:
                operation_latencies[latency_key] = endpoint_average_latency

        return operation_latencies

    def clean_up_telemetry_data(self):
        current_timestamp = time.time()
        copy_latencies = copy.deepcopy(self.latencies)

        for endpoint_name, endpoint_latencies in copy_latencies.items():
            for latency_information in endpoint_latencies:
                if current_timestamp - latency_information["timestamp"] > self.MAXIMUM_LATENCY_DATA_AGE:
                    self.latencies[endpoint_name].remove(latency_information)

            if len(self.latencies[endpoint_name]) == 0:
                del self.latencies[endpoint_name]

    def store_latency(self, latency, operation_type):
        if operation_type != PNOperationType.PNSubscribeOperation and latency > 0:
            endpoint_name = self.endpoint_name_for_operation(operation_type)

            store_timestamp = time.time()

            if endpoint_name not in self.latencies:
                self.latencies[endpoint_name] = []

            latency_entry = {
                "timestamp": store_timestamp,
                "latency": latency,
            }

            self.latencies[endpoint_name].append(latency_entry)

    @staticmethod
    def average_latency_from_data(endpoint_latencies):
        total_latency = 0

        for latency_data in endpoint_latencies:
            total_latency += latency_data['latency']

        return total_latency / len(endpoint_latencies)

    @staticmethod
    def endpoint_name_for_operation(operation_type):
        endpoint = {
            PNOperationType.PNPublishOperation: 'pub',
            PNOperationType.PNFireOperation: 'pub',

            PNOperationType.PNHistoryOperation: 'hist',
            PNOperationType.PNHistoryDeleteOperation: 'hist',
            PNOperationType.PNMessageCountOperation: 'mc',

            PNOperationType.PNUnsubscribeOperation: 'pres',
            PNOperationType.PNWhereNowOperation: 'pres',
            PNOperationType.PNHereNowOperation: 'pres',
            PNOperationType.PNGetState: 'pres',
            PNOperationType.PNSetStateOperation: 'pres',

            PNOperationType.PNAddChannelsToGroupOperation: 'cg',
            PNOperationType.PNRemoveChannelsFromGroupOperation: 'cg',
            PNOperationType.PNChannelGroupsOperation: 'cg',
            PNOperationType.PNChannelsForGroupOperation: 'cg',
            PNOperationType.PNRemoveGroupOperation: 'cg',

            PNOperationType.PNAddPushNotificationsOnChannelsOperation: 'push',
            PNOperationType.PNPushNotificationEnabledChannelsOperation: 'push',
            PNOperationType.PNRemoveAllPushNotificationsOperation: 'push',
            PNOperationType.PNRemovePushNotificationsFromChannelsOperation: 'push',

            PNOperationType.PNAccessManagerAudit: 'pam',
            PNOperationType.PNAccessManagerGrant: 'pam',
            PNOperationType.PNAccessManagerRevoke: 'pam',
            PNOperationType.PNTimeOperation: 'pam',

            PNOperationType.PNSignalOperation: 'sig',

            PNOperationType.PNSetUuidMetadataOperation: 'obj',
            PNOperationType.PNGetUuidMetadataOperation: 'obj',
            PNOperationType.PNRemoveUuidMetadataOperation: 'obj',
            PNOperationType.PNGetAllUuidMetadataOperation: 'obj',

            PNOperationType.PNSetChannelMetadataOperation: 'obj',
            PNOperationType.PNGetChannelMetadataOperation: 'obj',
            PNOperationType.PNRemoveChannelMetadataOperation: 'obj',
            PNOperationType.PNGetAllChannelMetadataOperation: 'obj',

            PNOperationType.PNSetChannelMembersOperation: 'obj',
            PNOperationType.PNGetChannelMembersOperation: 'obj',
            PNOperationType.PNRemoveChannelMembersOperation: 'obj',
            PNOperationType.PNManageChannelMembersOperation: 'obj',

            PNOperationType.PNSetMembershipsOperation: 'obj',
            PNOperationType.PNGetMembershipsOperation: 'obj',
            PNOperationType.PNRemoveMembershipsOperation: 'obj',
            PNOperationType.PNManageMembershipsOperation: 'obj',

            PNOperationType.PNAccessManagerGrantToken: 'pamv3',

            PNOperationType.PNAddMessageAction: 'msga',
            PNOperationType.PNGetMessageActions: 'msga',
            PNOperationType.PNDeleteMessageAction: 'msga',

            PNOperationType.PNGetFilesAction: 'file',
            PNOperationType.PNDeleteFileOperation: 'file',
            PNOperationType.PNGetFileDownloadURLAction: 'file',
            PNOperationType.PNFetchFileUploadS3DataAction: 'file',
            PNOperationType.PNDownloadFileAction: 'file',
            PNOperationType.PNSendFileAction: 'file',

        }[operation_type]

        return endpoint


class TokenManager(object):

    def __init__(self):
        self._map = {}
        self.init_map()

    def init_map(self):
        resources = [PNResourceType.USER, PNResourceType.SPACE]

        for resource in resources:
            skeleton_map = {
                PNMatchType.RESOURCE: {},
                PNMatchType.PATTERN: {}
            }
            self._map[resource] = skeleton_map

    def set_token(self, token):
        unwrapped_token = self.unwrap_token(token)
        self.store_token(unwrapped_token, token)

    def set_tokens(self, tokens):
        for token in tokens:
            self.set_token(token)

    def get_token(self, tms_properties):
        resource_token = self.get_token_by_match(tms_properties, PNMatchType.RESOURCE)

        if resource_token is None:
            return self.get_token_by_match(tms_properties, PNMatchType.PATTERN)

        return resource_token

    def get_tokens(self):
        return self._map

    def get_tokens_by_resource(self, resource_type):
        return self._map[resource_type]

    def store_token(self, unwrapped_token, token):
        match_types = [
            PNMatchType.RESOURCE,
            PNMatchType.PATTERN
        ]

        for asset in match_types:
            short_match_type = self.get_shortened_match_type(asset)

            if short_match_type in unwrapped_token:
                res_object = unwrapped_token[short_match_type]

                for r_type in res_object.keys():
                    single_res_object = res_object[r_type]
                    for r_name in single_res_object.keys():
                        if asset == PNMatchType.PATTERN:
                            self._map[self.get_extended_resource_type(r_type)][asset].clear()

                        self._map[self.get_extended_resource_type(r_type)][asset][r_name] = token

    def unwrap_token(self, token):
        raw = token

        raw = raw.replace("_", "/").replace("-", "+")
        byte_array = base64.b64decode(raw)

        try:
            unwrapped_obj = loads(byte_array)
            decoded_obj = utils.decode_utf8_dict(unwrapped_obj)

            return decoded_obj
        except Exception:
            raise PubNubException(pn_error=PNERR_INVALID_ACCESS_TOKEN)

    def get_token_by_match(self, tms_properties, match_type):
        if tms_properties is None or tms_properties.resource_type is None or tms_properties.resource_id is None:
            return None

        if match_type != PNMatchType.PATTERN:
            if tms_properties.resource_id in self._map[tms_properties.resource_type][match_type]:
                token = self._map[tms_properties.resource_type][match_type][tms_properties.resource_id]
                if token is not None:
                    return token
        else:
            string_token_wrapper_dict = self._map[tms_properties.resource_type][match_type]
            if len(string_token_wrapper_dict.keys()) > 0:
                first_key = list(string_token_wrapper_dict.keys())[0]
                return string_token_wrapper_dict[first_key]

        return None

    def get_extended_resource_type(self, r_type_abbr):
        if r_type_abbr == "usr":
            return PNResourceType.USER
        if r_type_abbr == "spc":
            return PNResourceType.SPACE

        return r_type_abbr

    def get_shortened_match_type(self, match_type):
        if match_type == PNMatchType.RESOURCE:
            return "res"
        if match_type == PNMatchType.PATTERN:
            return "pat"

        return match_type


class TokenManagerProperties:
    def __init__(self, resource_type, resource_id):
        self.resource_type = resource_type
        self.resource_id = resource_id

    def __str__(self):
        return "resource_type: " + self.resource_type + ", resource_id: " + self.resource_id
