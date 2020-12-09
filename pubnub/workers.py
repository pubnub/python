import logging

from abc import abstractmethod

from .enums import PNStatusCategory, PNOperationType
from .models.consumer.common import PNStatus
from .models.consumer.objects_v2.channel import PNChannelMetadataResult
from .models.consumer.objects_v2.memberships import PNMembershipResult
from .models.consumer.objects_v2.uuid import PNUUIDMetadataResult
from .models.consumer.pn_error_data import PNErrorData
from .utils import strip_right
from .models.consumer.pubsub import (
    PNPresenceEventResult, PNMessageResult, PNSignalMessageResult, PNMessageActionResult, PNFileMessageResult
)
from .models.server.subscribe import SubscribeMessage, PresenceEnvelope
from .endpoints.file_operations.get_file_url import GetFileDownloadUrl


logger = logging.getLogger("pubnub")


class SubscribeMessageWorker(object):
    TYPE_MESSAGE = 0
    TYPE_SIGNAL = 1
    TYPE_OBJECT = 2
    TYPE_MESSAGE_ACTION = 3
    TYPE_FILE_MESSAGE = 4

    def __init__(self, pubnub_instance, listener_manager_instance, queue_instance, event):
        # assert isinstance(pubnub_instnace, PubNubCore)
        # assert isinstance(listener_manager_instance, ListenerManager)
        # assert isinstance(queue_instance, utils.Queue)

        self._pubnub = pubnub_instance
        self._listener_manager = listener_manager_instance
        self._queue = queue_instance
        self._is_running = None
        self._event = event

    def run(self):
        self._take_message()

    @abstractmethod
    def _take_message(self):
        pass

    def _get_url_for_file_event_message(self, channel, extracted_message):
        return GetFileDownloadUrl(self._pubnub)\
            .channel(channel) \
            .file_name(extracted_message["file"]["name"])\
            .file_id(extracted_message["file"]["id"]).get_complete_url()

    def _process_message(self, message_input):
        if self._pubnub.config.cipher_key is None:
            return message_input
        else:
            try:
                return self._pubnub.config.crypto.decrypt(
                    self._pubnub.config.cipher_key,
                    message_input
                )
            except Exception as exception:
                logger.warning("could not decrypt message: \"%s\", due to error %s" % (message_input, str(exception)))
                pn_status = PNStatus()
                pn_status.category = PNStatusCategory.PNDecryptionErrorCategory
                pn_status.error_data = PNErrorData(str(exception), exception)
                pn_status.error = True
                pn_status.operation = PNOperationType.PNSubscribeOperation
                self._listener_manager.announce_status(pn_status)
                return message_input

    def _process_incoming_payload(self, message):
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
            self._listener_manager.announce_presence(pn_presence_event_result)
        elif message.type == SubscribeMessageWorker.TYPE_OBJECT:
            if message.payload['type'] == 'channel':
                channel_result = PNChannelMetadataResult(
                    event=message.payload['event'],
                    data=message.payload['data']
                )
                self._listener_manager.announce_channel(channel_result)
            elif message.payload['type'] == 'uuid':
                uuid_result = PNUUIDMetadataResult(
                    event=message.payload['event'],
                    data=message.payload['data']
                )
                self._listener_manager.announce_uuid(uuid_result)
            elif message.payload['type'] == 'membership':
                membership_result = PNMembershipResult(
                    event=message.payload['event'],
                    data=message.payload['data']
                )
                self._listener_manager.announce_membership(membership_result)
        elif message.type == SubscribeMessageWorker.TYPE_FILE_MESSAGE:
            extracted_message = self._process_message(message.payload)
            download_url = self._get_url_for_file_event_message(channel, extracted_message)

            pn_file_result = PNFileMessageResult(
                message=extracted_message.get("message"),
                channel=channel,
                subscription=subscription_match,
                timetoken=publish_meta_data.publish_timetoken,
                publisher=message.issuing_client_id,
                file_url=download_url,
                file_id=extracted_message["file"]["id"],
                file_name=extracted_message["file"]["name"]
            )

            self._listener_manager.announce_file_message(pn_file_result)

        else:
            extracted_message = self._process_message(message.payload)
            publisher = message.issuing_client_id

            if extracted_message is None:
                logger.debug("unable to parse payload on #processIncomingMessages")

            if message.type == SubscribeMessageWorker.TYPE_SIGNAL:
                pn_signal_result = PNSignalMessageResult(
                    message=extracted_message,
                    channel=channel,
                    subscription=subscription_match,
                    timetoken=publish_meta_data.publish_timetoken,
                    publisher=publisher
                )
                self._listener_manager.announce_signal(pn_signal_result)

            elif message.type == SubscribeMessageWorker.TYPE_MESSAGE_ACTION:
                message_action = extracted_message['data']
                if 'uuid' not in message_action:
                    message_action['uuid'] = publisher

                message_action_result = PNMessageActionResult(message_action)
                self._listener_manager.announce_message_action(message_action_result)

            else:
                pn_message_result = PNMessageResult(
                    message=extracted_message,
                    channel=channel,
                    subscription=subscription_match,
                    timetoken=publish_meta_data.publish_timetoken,
                    publisher=publisher
                )
                self._listener_manager.announce_message(pn_message_result)
