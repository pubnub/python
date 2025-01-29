import logging

from abc import abstractmethod
from typing import Union

from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.managers import ListenerManager
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel import PNChannelMetadataResult
from pubnub.models.consumer.objects_v2.memberships import PNMembershipResult
from pubnub.models.consumer.objects_v2.uuid import PNUUIDMetadataResult
from pubnub.models.consumer.pn_error_data import PNErrorData
from pubnub.utils import strip_right
from pubnub.models.consumer.pubsub import (
    PNPresenceEventResult, PNMessageResult, PNSignalMessageResult, PNMessageActionResult, PNFileMessageResult
)
from pubnub.models.server.subscribe import SubscribeMessage, PresenceEnvelope
from pubnub.endpoints.file_operations.get_file_url import GetFileDownloadUrl


logger = logging.getLogger("pubnub")


class BaseMessageWorker:
    # _pubnub: PubNub
    _listener_manager: Union[ListenerManager, None] = None

    TYPE_MESSAGE = 0
    TYPE_SIGNAL = 1
    TYPE_OBJECT = 2
    TYPE_MESSAGE_ACTION = 3
    TYPE_FILE_MESSAGE = 4

    def __init__(self, pubnub_instance) -> None:
        self._pubnub = pubnub_instance

    def _get_url_for_file_event_message(self, channel, extracted_message):
        return GetFileDownloadUrl(self._pubnub)\
            .channel(channel) \
            .file_name(extracted_message["file"]["name"])\
            .file_id(extracted_message["file"]["id"]).get_complete_url()

    def _process_message(self, message_input):
        if self._pubnub.config.cipher_key is None:
            return message_input, None
        else:
            try:
                return self._pubnub.crypto.decrypt(message_input), None
            except Exception as exception:
                logger.warning("could not decrypt message: \"%s\", due to error %s" % (message_input, str(exception)))

                pn_status = PNStatus()
                pn_status.category = PNStatusCategory.PNDecryptionErrorCategory
                pn_status.error_data = PNErrorData(str(exception), exception)
                pn_status.error = True
                pn_status.operation = PNOperationType.PNSubscribeOperation
                self.announce(pn_status)
                return message_input, exception

    def announce(self, result):
        if not self._listener_manager:
            return

        if isinstance(result, PNStatus):
            self._listener_manager.announce_status(result)

        elif isinstance(result, PNPresenceEventResult):
            self._listener_manager.announce_presence(result)

        elif isinstance(result, PNChannelMetadataResult):
            self._listener_manager.announce_channel(result)

        elif isinstance(result, PNUUIDMetadataResult):
            self._listener_manager.announce_uuid(result)

        elif isinstance(result, PNMembershipResult):
            self._listener_manager.announce_membership(result)

        elif isinstance(result, PNFileMessageResult):
            self._listener_manager.announce_file_message(result)

        elif isinstance(result, PNSignalMessageResult):
            self._listener_manager.announce_signal(result)

        elif isinstance(result, PNMessageActionResult):
            self._listener_manager.announce_message_action(result)

        elif isinstance(result, PNMessageResult):
            self._listener_manager.announce_message(result)

    def _process_incoming_payload(self, message: SubscribeMessage):
        assert isinstance(message, SubscribeMessage)

        channel = message.channel
        subscription_match = message.subscription_match
        publish_meta_data = message.publish_metadata

        if channel is not None and channel == subscription_match:
            subscription_match = None

        if "-pnpres" in message.channel:
            presence_payload = PresenceEnvelope.from_json_payload(message.payload)

            stripped_presence_channel = None
            stripped_presence_subscription = None

            if channel is not None:
                stripped_presence_channel = strip_right(channel, "-pnpres")

            if subscription_match is not None:
                stripped_presence_subscription = strip_right(subscription_match, "-pnpres")

            pn_presence_event_result = PNPresenceEventResult(
                event=presence_payload.action,
                channel=stripped_presence_channel,
                subscription=stripped_presence_subscription,
                timetoken=publish_meta_data.publish_timetoken,
                occupancy=presence_payload.occupancy,
                uuid=presence_payload.uuid,
                timestamp=presence_payload.timestamp,
                state=presence_payload.data,
                join=message.payload.get('join', None),
                leave=message.payload.get('leave', None),
                timeout=message.payload.get('timeout', None)
            )

            self.announce(pn_presence_event_result)
            return pn_presence_event_result

        elif message.type == SubscribeMessageWorker.TYPE_OBJECT:
            if message.payload['type'] == 'channel':
                channel_result = PNChannelMetadataResult(
                    event=message.payload['event'],
                    data=message.payload['data']
                )
                self.announce(channel_result)
                return channel_result

            elif message.payload['type'] == 'uuid':
                uuid_result = PNUUIDMetadataResult(
                    event=message.payload['event'],
                    data=message.payload['data']
                )
                self.announce(uuid_result)
                return uuid_result

            elif message.payload['type'] == 'membership':
                membership_result = PNMembershipResult(
                    event=message.payload['event'],
                    data=message.payload['data']
                )
                self.announce(membership_result)
                return membership_result

        elif message.type == SubscribeMessageWorker.TYPE_FILE_MESSAGE:
            extracted_message, _ = self._process_message(message.payload)
            download_url = self._get_url_for_file_event_message(channel, extracted_message)

            pn_file_result = PNFileMessageResult(
                message=extracted_message.get("message"),
                channel=channel,
                subscription=subscription_match,
                timetoken=publish_meta_data.publish_timetoken,
                publisher=message.issuing_client_id,
                custom_message_type=message.custom_message_type,
                user_metadata=message.user_metadata,
                file_url=download_url,
                file_id=extracted_message["file"]["id"],
                file_name=extracted_message["file"]["name"]
            )
            self.announce(pn_file_result)
            return pn_file_result

        else:
            extracted_message, error = self._process_message(message.payload)
            publisher = message.issuing_client_id

            if extracted_message is None:
                logger.debug("unable to parse payload on #processIncomingMessages")

            if message.type == SubscribeMessageWorker.TYPE_SIGNAL:
                pn_signal_result = PNSignalMessageResult(
                    message=extracted_message,
                    channel=channel,
                    subscription=subscription_match,
                    timetoken=publish_meta_data.publish_timetoken,
                    publisher=publisher,
                    custom_message_type=message.custom_message_type,
                    user_metadata=message.user_metadata,
                    error=error
                )
                self.announce(pn_signal_result)
                return pn_signal_result

            elif message.type == SubscribeMessageWorker.TYPE_MESSAGE_ACTION:
                message_action = extracted_message['data']
                if 'uuid' not in message_action:
                    message_action['uuid'] = publisher
                message_action_result = PNMessageActionResult(message_action, subscription=subscription_match,
                                                              channel=channel)
                self._listener_manager.announce_message_action(message_action_result)

            else:
                pn_message_result = PNMessageResult(
                    message=extracted_message,
                    channel=channel,
                    subscription=subscription_match,
                    timetoken=publish_meta_data.publish_timetoken,
                    publisher=publisher,
                    custom_message_type=message.custom_message_type,
                    user_metadata=message.user_metadata,
                    error=error
                )
                self.announce(pn_message_result)
                return pn_message_result


class SubscribeMessageWorker(BaseMessageWorker):
    def __init__(self, pubnub_instance, listener_manager_instance, queue_instance, event):
        # assert isinstance(pubnub_instnace, PubNubCore)
        # assert isinstance(listener_manager_instance, ListenerManager)
        # assert isinstance(queue_instance, utils.Queue)
        super().__init__(pubnub_instance)
        self._listener_manager = listener_manager_instance
        self._queue = queue_instance
        self._is_running = None
        self._event = event

    def run(self):
        self._take_message()

    @abstractmethod
    def _take_message(self):
        pass
