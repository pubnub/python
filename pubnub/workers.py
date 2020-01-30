import logging

from abc import abstractmethod
from .utils import strip_right
from .models.consumer.pubsub import PNPresenceEventResult, PNMessageResult, PNSignalMessageResult, PNMessageActionResult
from .models.server.subscribe import SubscribeMessage, PresenceEnvelope
from .models.consumer.user import PNUserResult
from .models.consumer.space import PNSpaceResult
from .models.consumer.membership import PNMembershipResult

logger = logging.getLogger("pubnub")


class SubscribeMessageWorker(object):
    TYPE_MESSAGE = 0
    TYPE_SIGNAL = 1
    TYPE_OBJECT = 2
    TYPE_MESSAGE_ACTION = 3

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

    def _process_message(self, message_input):
        if self._pubnub.config.cipher_key is None:
            return message_input
        else:
            return self._pubnub.config.crypto.decrypt(self._pubnub.config.cipher_key, message_input)

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
            if message.payload['type'] == 'user':
                user_result = PNUserResult(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
                    event=message.payload['event'],
                    data=message.payload['data']
                )
                self._listener_manager.announce_user(user_result)
            elif message.payload['type'] == 'space':
                space_result = PNSpaceResult(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
                    event=message.payload['event'],
                    data=message.payload['data']
                )
                self._listener_manager.announce_space(space_result)
            else:
                membership_result = PNMembershipResult(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
                    event=message.payload['event'],
                    data=message.payload['data']
                )
                self._listener_manager.announce_membership(membership_result)
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
