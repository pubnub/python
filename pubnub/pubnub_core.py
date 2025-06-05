"""PubNub Core SDK Implementation.

This module implements the core functionality of the PubNub Python SDK. It provides
a comprehensive interface for real-time communication features including:

- Publish/Subscribe Messaging
- Presence Detection
- Channel Groups
- Message Storage and Playback
- Push Notifications
- Stream Controllers
- Message Actions
- File Sharing
- Access Management

The PubNubCore class serves as the base implementation, providing all core functionality
while allowing platform-specific implementations (like synchronous vs asynchronous)
to extend it.

Typical usage:
    ```python
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub

    config = PNConfiguration()
    config.publish_key = 'your_pub_key'
    config.subscribe_key = 'your_sub_key'
    config.uuid = 'client-123'

    pubnub = PubNub(config)

    # Publishing
    pubnub.publish().channel("chat").message({"text": "Hello!"}).sync()

    # Subscribing
    def my_listener(message, event):
        print(f"Received: {message.message}")

    pubnub.add_listener(my_listener)
    pubnub.subscribe().channels("chat").execute()
    ```

Implementation Notes:
    - All methods return builder objects that can be chained
    - Synchronous operations end with .sync()
    - Asynchronous implementations may provide different execution methods
    - Error handling is done through PubNubException
    - Configuration is immutable by default for thread safety

See Also:
    - PNConfiguration: For SDK configuration options
    - PubNub: For the main implementation
    - PubNubAsyncio: For the asynchronous implementation
    - SubscribeCallback: For handling subscription events
"""

import logging
import time
from warnings import warn
from copy import deepcopy
from typing import Dict, List, Optional, Union, Any, TYPE_CHECKING
from pubnub.endpoints.entities.membership.add_memberships import AddSpaceMembers, AddUserSpaces
from pubnub.endpoints.entities.membership.update_memberships import UpdateSpaceMembers, UpdateUserSpaces
from pubnub.endpoints.entities.membership.fetch_memberships import FetchSpaceMemberships, FetchUserMemberships
from pubnub.endpoints.entities.membership.remove_memberships import RemoveSpaceMembers, RemoveUserSpaces

from pubnub.endpoints.entities.space.update_space import UpdateSpace
from pubnub.endpoints.entities.user.create_user import CreateUser
from pubnub.endpoints.entities.space.remove_space import RemoveSpace
from pubnub.endpoints.entities.space.fetch_spaces import FetchSpaces
from pubnub.endpoints.entities.space.fetch_space import FetchSpace
from pubnub.endpoints.entities.space.create_space import CreateSpace
from pubnub.endpoints.entities.user.remove_user import RemoveUser
from pubnub.endpoints.entities.user.update_user import UpdateUser
from pubnub.endpoints.entities.user.fetch_user import FetchUser
from pubnub.endpoints.entities.user.fetch_users import FetchUsers
from pubnub.enums import PNPushEnvironment, PNPushType
from pubnub.errors import PNERR_MISUSE_OF_USER_AND_SPACE, PNERR_USER_SPACE_PAIRS_MISSING
from pubnub.exceptions import PubNubException
from pubnub.features import feature_flag
from pubnub.crypto import PubNubCryptoModule
from pubnub.models.consumer.message_actions import PNMessageAction
from pubnub.models.consumer.objects_v2.channel_members import PNUUID
from pubnub.models.consumer.objects_v2.common import MemberIncludes, MembershipIncludes
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.models.subscription import PubNubChannel, PubNubChannelGroup, PubNubChannelMetadata, PubNubUserMetadata, \
    PNSubscriptionRegistry, PubNubSubscriptionSet

from abc import ABCMeta, abstractmethod

from pubnub.pnconfiguration import PNConfiguration

from pubnub.endpoints.objects_v2.uuid.set_uuid import SetUuid
from pubnub.endpoints.objects_v2.channel.get_all_channels import GetAllChannels
from pubnub.endpoints.objects_v2.channel.get_channel import GetChannel
from pubnub.endpoints.objects_v2.channel.remove_channel import RemoveChannel
from pubnub.endpoints.objects_v2.channel.set_channel import SetChannel
from pubnub.endpoints.objects_v2.members.get_channel_members import GetChannelMembers
from pubnub.endpoints.objects_v2.members.manage_channel_members import ManageChannelMembers
from pubnub.endpoints.objects_v2.members.remove_channel_members import RemoveChannelMembers
from pubnub.endpoints.objects_v2.members.set_channel_members import SetChannelMembers
from pubnub.endpoints.objects_v2.memberships.get_memberships import GetMemberships
from pubnub.endpoints.objects_v2.memberships.manage_memberships import ManageMemberships
from pubnub.endpoints.objects_v2.memberships.remove_memberships import RemoveMemberships
from pubnub.endpoints.objects_v2.memberships.set_memberships import SetMemberships
from pubnub.endpoints.objects_v2.uuid.get_all_uuid import GetAllUuid
from pubnub.endpoints.objects_v2.uuid.get_uuid import GetUuid
from pubnub.endpoints.objects_v2.uuid.remove_uuid import RemoveUuid
from pubnub.managers import BasePathManager, TokenManager
from pubnub.builders import SubscribeBuilder
from pubnub.builders import UnsubscribeBuilder
from pubnub.endpoints.time import Time
from pubnub.endpoints.history import History
from pubnub.endpoints.access.audit import Audit
from pubnub.endpoints.access.grant import Grant
from pubnub.endpoints.access.grant_token import GrantToken
from pubnub.endpoints.access.revoke_token import RevokeToken
from pubnub.endpoints.channel_groups.add_channel_to_channel_group import AddChannelToChannelGroup
from pubnub.endpoints.channel_groups.list_channels_in_channel_group import ListChannelsInChannelGroup
from pubnub.endpoints.channel_groups.remove_channel_from_channel_group import RemoveChannelFromChannelGroup
from pubnub.endpoints.channel_groups.remove_channel_group import RemoveChannelGroup
from pubnub.endpoints.presence.get_state import GetState
from pubnub.endpoints.presence.heartbeat import Heartbeat
from pubnub.endpoints.presence.set_state import SetState
from pubnub.endpoints.pubsub.publish import Publish
from pubnub.endpoints.pubsub.fire import Fire
from pubnub.endpoints.presence.here_now import HereNow
from pubnub.endpoints.presence.where_now import WhereNow
from pubnub.endpoints.history_delete import HistoryDelete
from pubnub.endpoints.message_count import MessageCount
from pubnub.endpoints.signal import Signal
from pubnub.endpoints.fetch_messages import FetchMessages
from pubnub.endpoints.message_actions.add_message_action import AddMessageAction
from pubnub.endpoints.message_actions.get_message_actions import GetMessageActions
from pubnub.endpoints.message_actions.remove_message_action import RemoveMessageAction
from pubnub.endpoints.file_operations.list_files import ListFiles
from pubnub.endpoints.file_operations.delete_file import DeleteFile
from pubnub.endpoints.file_operations.get_file_url import GetFileDownloadUrl
from pubnub.endpoints.file_operations.fetch_upload_details import FetchFileUploadS3Data
from pubnub.endpoints.file_operations.send_file import SendFileNative
from pubnub.endpoints.file_operations.download_file import DownloadFileNative
from pubnub.endpoints.file_operations.publish_file_message import PublishFileMessage

from pubnub.endpoints.push.add_channels_to_push import AddChannelsToPush
from pubnub.endpoints.push.remove_channels_from_push import RemoveChannelsFromPush
from pubnub.endpoints.push.remove_device import RemoveDeviceFromPush
from pubnub.endpoints.push.list_push_provisions import ListPushProvisions
from pubnub.managers import TelemetryManager

if TYPE_CHECKING:
    from pubnub.endpoints.file_operations.send_file_asyncio import AsyncioSendFile
    from pubnub.endpoints.file_operations.download_file_asyncio import DownloadFileAsyncio

logger = logging.getLogger("pubnub")


class PubNubCore:
    """A base class for PubNub Python API implementations.

    This class provides the core functionality for interacting with the PubNub real-time network.
    It includes methods for publishing/subscribing to channels, managing presence, handling files,
    and dealing with access control.
    """

    SDK_VERSION: str = "10.4.0"
    SDK_NAME: str = "PubNub-Python"

    TIMESTAMP_DIVIDER: int = 1000
    MAX_SEQUENCE: int = 65535

    __metaclass__ = ABCMeta
    __crypto: Optional[PubNubCryptoModule] = None

    _subscription_registry: PNSubscriptionRegistry

    def __init__(self, config: PNConfiguration) -> None:
        """Initialize a new PubNub instance.

        Args:
            config (PNConfiguration): Configuration instance containing settings like
                publish/subscribe keys, UUID, and other operational parameters.
        """
        if not config.disable_config_locking:
            config.lock()
            self.config = deepcopy(config)
        else:
            self.config = config
        self.config.validate()
        self.headers: Dict[str, str] = {
            'User-Agent': self.sdk_name
        }

        self._subscription_manager = None
        self._publish_sequence_manager = None
        self._telemetry_manager = TelemetryManager()
        self._base_path_manager = BasePathManager(config)
        self._token_manager = TokenManager()
        self._subscription_registry = PNSubscriptionRegistry(self)

    @property
    def base_origin(self) -> str:
        return self._base_path_manager.get_base_path()

    @property
    def sdk_name(self) -> str:
        return "%s%s/%s" % (PubNubCore.SDK_NAME, self.sdk_platform(), PubNubCore.SDK_VERSION)

    @abstractmethod
    def sdk_platform(self) -> str:
        pass

    @property
    def uuid(self) -> str:
        return self.config.uuid

    @property
    def crypto(self) -> Optional[PubNubCryptoModule]:
        crypto_module = self.__crypto or self.config.crypto_module
        if not crypto_module and self.config.cipher_key:
            crypto_module = self.config.DEFAULT_CRYPTO_MODULE(self.config)
        return crypto_module

    @crypto.setter
    def crypto(self, crypto: PubNubCryptoModule) -> None:
        self.__crypto = crypto

    def add_listener(self, listener: Any) -> None:
        """Add a listener for subscribe events.

        The listener will receive callbacks for messages, presence events,
        and status updates.

        Args:
            listener (Any): An object implementing the necessary callback methods
                for handling subscribe events.

        Raises:
            Exception: If subscription manager is not enabled.

        Example:
            ```python
            class MyListener(SubscribeCallback):
                def message(self, pubnub, message):
                    print(f"Received message: {message.message}")

            pubnub.add_listener(MyListener())
            ```
        """
        self._validate_subscribe_manager_enabled()
        return self._subscription_manager.add_listener(listener)

    def remove_listener(self, listener: Any) -> None:
        """Remove a listener from the subscription manager.

        Args:
            listener (Any): The listener to remove.

        Returns:
            None

        Example:
            ```python
            pubnub.remove_listener(MyListener())
            ```
        """

        self._validate_subscribe_manager_enabled()
        return self._subscription_manager.remove_listener(listener)

    def get_subscribed_channels(self) -> List[str]:
        self._validate_subscribe_manager_enabled()
        return self._subscription_manager.get_subscribed_channels()

    def get_subscribed_channel_groups(self) -> List[str]:
        self._validate_subscribe_manager_enabled()
        return self._subscription_manager.get_subscribed_channel_groups()

    def add_channel_to_channel_group(self, channels: Union[str, List[str]] = None,
                                     channel_group: str = None) -> AddChannelToChannelGroup:
        """Add channels to a channel group.

        Channel groups allow you to group multiple channels under a single
        subscription point.

        Args:
            channels: Channel(s) to add to the group.
            channel_group (str, optional): The name of the channel group.

        Returns:
            AddChannelToChannelGroup: An AddChannelToChannelGroup object that can
            be used to execute the request.

        Example:
            ```python
            pubnub.add_channel_to_channel_group(
                channels=["chat-1", "chat-2"],
                channel_group="all-chats"
            ).sync()
            ```
        """
        return AddChannelToChannelGroup(self, channels=channels, channel_group=channel_group)

    def remove_channel_from_channel_group(self, channels: Union[str, List[str]] = None,
                                          channel_group: str = None) -> RemoveChannelFromChannelGroup:
        """Remove channels from a channel group.

        Removes specified channels from a channel group subscription point.

        Args:
            channels: Channel(s) to remove from the group.
            channel_group (str, optional): The name of the channel group.

        Returns:
            RemoveChannelFromChannelGroup: A RemoveChannelFromChannelGroup object
            that can be used to execute the request.

        Example:
            ```python
            pubnub.remove_channel_from_channel_group(
                channels="chat-1",
                channel_group="all-chats"
            ).sync()
            ```
        """
        return RemoveChannelFromChannelGroup(self, channels=channels, channel_group=channel_group)

    def list_channels_in_channel_group(self, channel_group: str = None) -> ListChannelsInChannelGroup:
        """List all channels in a channel group.

        Retrieves all channels that are members of the specified channel group.

        Args:
            channel_group (str, optional): The name of the channel group.

        Returns:
            ListChannelsInChannelGroup: A ListChannelsInChannelGroup object that
            can be used to execute the request.

        Example:
            ```python
            result = pubnub.list_channels_in_channel_group(
                channel_group="all-chats"
            ).sync()
            print(f"Channels in group: {result.channels}")
            ```
        """
        return ListChannelsInChannelGroup(self, channel_group=channel_group)

    def remove_channel_group(self) -> RemoveChannelGroup:
        """Remove a channel group.

        Removes a channel group from the PubNub network.

        Returns:
            RemoveChannelGroup: A RemoveChannelGroup object that can be used to
            execute the request.

        Example:
            ```python
            pubnub.remove_channel_group().sync()
            ```
        """
        return RemoveChannelGroup(self)

    def subscribe(self) -> SubscribeBuilder:
        """Create a new subscription to channels or channel groups.

        Returns:
            SubscribeBuilder: A builder object for configuring the subscription.

        Example:
            ```python
            pubnub.subscribe() \
                .channels("my_channel") \
                .with_presence() \
                .execute()
            ```
        """
        return SubscribeBuilder(self)

    def unsubscribe(self) -> UnsubscribeBuilder:
        """Create a new unsubscribe request.

        Returns:
            UnsubscribeBuilder: A builder object for configuring the unsubscribe.

        Example:
            ```python
            pubnub.unsubscribe() \
                .channels("my_channel") \
                .execute()
            ```
        """
        return UnsubscribeBuilder(self)

    def unsubscribe_all(self) -> None:
        """Unsubscribe from all channels and channel groups.

        Removes all current subscriptions from the PubNub instance.

        Returns:
            None

        Example:
            ```python
            pubnub.unsubscribe_all()
            ```
        """
        return self._subscription_registry.unsubscribe_all()

    def reconnect(self) -> None:
        return self._subscription_registry.reconnect()

    def heartbeat(self) -> Heartbeat:
        """Send a heartbeat signal to the PubNub network.

        Updates presence information for the current user in subscribed channels.
        This is typically handled automatically by the SDK but can be manually
        triggered if needed.

        Returns:
            Heartbeat: A Heartbeat object that can be used to execute the request.

        Note:
            Manual heartbeats are rarely needed as the SDK handles presence
            automatically when subscribing to channels with presence enabled.
        """
        return Heartbeat(self)

    def set_state(self, channels: Union[str, List[str]] = None, channel_groups: Union[str, List[str]] = None,
                  state: Optional[Dict[str, Any]] = None) -> SetState:
        """Set state data for a subscriber.

        Sets state information for the current subscriber on specified channels
        or channel groups.

        Args:
            channels: Channel(s) to set state for.
            channel_groups: Channel group(s) to set state for.
            state: Dictionary containing state information.

        Returns:
            SetState: A SetState object that can be used to execute the request.

        Example:
            ```python
            pubnub.set_state(
                channels=["game"],
                state={"level": 5, "health": 100}
            ).sync()
            ```
        """
        return SetState(self, self._subscription_manager, channels, channel_groups, state)

    def get_state(self, channels: Union[str, List[str]] = None, channel_groups: Union[str, List[str]] = None,
                  uuid: Optional[str] = None) -> GetState:
        """Get the current state for a user.

        Retrieves the metadata associated with a user's presence in specified
        channels or channel groups.

        Args:
            channels: Channel(s) to get state from.
            channel_groups: Channel group(s) to get state from.
            uuid (str, optional): The UUID of the user to get state for.
                If not provided, uses the UUID of the current instance.

        Returns:
            GetState: A GetState object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.get_state(
                channels=["game"],
                uuid="player123"
            ).sync()
            print(f"Player state: {result.state}")
            ```
        """
        return GetState(self, channels, channel_groups, uuid)

    def here_now(self, channels: Union[str, List[str]] = None, channel_groups: Union[str, List[str]] = None,
                 include_state: bool = False, include_uuids: bool = True) -> HereNow:
        """Get presence information for channels and channel groups.

        Retrieves information about subscribers currently present in specified
        channels and channel groups.

        Args:
            channels: Channel(s) to get presence info for.
            channel_groups: Channel group(s) to get presence info for.
            include_state: Whether to include subscriber state information.
            include_uuids: Whether to include subscriber UUIDs.

        Returns:
            HereNow: A HereNow object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.here_now(
                channels=["lobby"],
                include_state=True
            ).sync()
            print(f"Active users: {result.total_occupancy}")
            ```
        """
        return HereNow(self, channels, channel_groups, include_state, include_uuids)

    def where_now(self, user_id: Optional[str] = None) -> WhereNow:
        """Get presence information for a specific user.

        Retrieves a list of channels the specified user is currently subscribed to.

        Args:
            user_id (str, optional): The UUID of the user to get presence info for.
                If not provided, uses the UUID of the current instance.

        Returns:
            WhereNow: A WhereNow object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.where_now(user_id="user123").sync()
            print(f"User is in channels: {result.channels}")
            ```
        """
        return WhereNow(self, user_id)

    def publish(self, channel: str = None, message: Any = None, should_store: Optional[bool] = None,
                use_post: Optional[bool] = None, meta: Optional[Any] = None, replicate: Optional[bool] = None,
                ptto: Optional[int] = None, ttl: Optional[int] = None, custom_message_type: Optional[str] = None
                ) -> Publish:
        """Publish a message to a channel.

        Sends a message to all channel subscribers. Messages are replicated across PubNub's
        points of presence and delivered to all subscribed clients simultaneously.

        Args:
            channel (str, optional): The channel to publish to.
            message (Any, optional): The message to publish. Can be any JSON-serializable type.
            should_store (bool, optional): Whether to store the message in history.
            use_post (bool, optional): Whether to use POST instead of GET for the request.
            meta (Any, optional): Additional metadata to attach to the message.
            replicate (bool, optional): Whether to replicate the message across data centers.
            ptto (int, optional): Publish TimeToken Override - Timestamp for the message.
            ttl (int, optional): Time to live in minutes for the message.
            custom_message_type (str, optional): Custom message type identifier.

        Returns:
            Publish: A Publish object that can be used to execute the request.

        Example:
            ```python
            pubnub.publish(
                channel="my_channel",
                message={"text": "Hello, World!"},
                meta={"sender": "python-sdk"}
            ).sync()
            ```
        """
        return Publish(self, channel=channel, message=message, should_store=should_store, use_post=use_post, meta=meta,
                       replicate=replicate, ptto=ptto, ttl=ttl, custom_message_type=custom_message_type)

    def grant(self) -> Grant:
        """ Deprecated. Use grant_token instead """
        warn("Access management v2 is being deprecated. We recommend switching to grant_token().",
             DeprecationWarning, stacklevel=2)
        return Grant(self)

    def grant_token(
        self,
        channels: Union[str, List[str]] = None,
        channel_groups: Union[str, List[str]] = None,
        users: Union[str, List[str]] = None,
        spaces: Union[str, List[str]] = None,
        authorized_user_id: str = None,
        ttl: Optional[int] = None,
        meta: Optional[Any] = None
    ) -> GrantToken:
        return GrantToken(
            self,
            channels=channels,
            channel_groups=channel_groups,
            users=users,
            spaces=spaces,
            authorized_user_id=authorized_user_id,
            ttl=ttl,
            meta=meta
        )

    def revoke_token(self, token: str) -> RevokeToken:
        return RevokeToken(self, token)

    def audit(self) -> Audit:
        """ Deprecated """
        warn("Access management v2 is being deprecated.", DeprecationWarning, stacklevel=2)
        return Audit(self)

    # Push Related methods
    def list_push_channels(self, device_id: str = None, push_type: PNPushType = None, topic: str = None,
                           environment: PNPushEnvironment = None) -> ListPushProvisions:
        """List channels registered for push notifications.

        Retrieves a list of channels that are registered for push notifications
        for a specific device.

        Args:
            device_id (str, optional): The device token/ID to list channels for.
            push_type (PNPushType, optional): The type of push notification service
                (e.g., APNS, FCM).
            topic (str, optional): The topic for APNS notifications.
            environment (PNPushEnvironment, optional): The environment for APNS
                (production or development).

        Returns:
            ListPushProvisions: A ListPushProvisions object that can be used to
            execute the request.

        Example:
            ```python
            from pubnub.enums import PNPushType

            result = pubnub.list_push_channels(
                device_id="device_token",
                push_type=PNPushType.APNS
            ).sync()
            print(f"Registered channels: {result.channels}")
            ```
        """
        return ListPushProvisions(self, device_id=device_id, push_type=push_type, topic=topic, environment=environment)

    def add_channels_to_push(self, channels: Union[str, List[str]] = None, device_id: str = None,
                             push_type: PNPushType = None, topic: str = None,
                             environment: PNPushEnvironment = None) -> AddChannelsToPush:
        """Register channels for push notifications.

        Enables push notifications for specified channels on a device.

        Args:
            channels: Channel(s) to enable push notifications for.
            device_id (str, optional): The device token/ID to register.
            push_type (PNPushType, optional): The type of push notification service.
            topic (str, optional): The topic for APNS notifications.
            environment (PNPushEnvironment, optional): The environment for APNS.

        Returns:
            AddChannelsToPush: An AddChannelsToPush object that can be used to
            execute the request.

        Example:
            ```python
            from pubnub.enums import PNPushType

            pubnub.add_channels_to_push(
                channels=["alerts", "news"],
                device_id="device_token",
                push_type=PNPushType.FCM
            ).sync()
            ```
        """
        return AddChannelsToPush(self, channels=channels, device_id=device_id, push_type=push_type, topic=topic,
                                 environment=environment)

    def remove_channels_from_push(self, channels: Union[str, List[str]] = None, device_id: str = None,
                                  push_type: PNPushType = None, topic: str = None,
                                  environment: PNPushEnvironment = None) -> RemoveChannelsFromPush:
        """Unregister channels from push notifications.

        Disables push notifications for specified channels on a device.

        Args:
            channels: Channel(s) to disable push notifications for.
            device_id (str, optional): The device token/ID.
            push_type (PNPushType, optional): The type of push notification service.
            topic (str, optional): The topic for APNS notifications.
            environment (PNPushEnvironment, optional): The environment for APNS.

        Returns:
            RemoveChannelsFromPush: A RemoveChannelsFromPush object that can be
            used to execute the request.

        Example:
            ```python
            pubnub.remove_channels_from_push(
                channels=["alerts"],
                device_id="device_token",
                push_type=PNPushType.FCM
            ).sync()
            ```
        """
        return RemoveChannelsFromPush(self, channels=channels, device_id=device_id, push_type=push_type, topic=topic,
                                      environment=environment)

    def remove_device_from_push(self, device_id: str = None, push_type: PNPushType = None,
                                topic: str = None, environment: PNPushEnvironment = None) -> RemoveDeviceFromPush:
        """Unregister a device from all push notifications.

        Removes all push notification registrations for a device.

        Args:
            device_id (str, optional): The device token/ID to unregister.
            push_type (PNPushType, optional): The type of push notification service.
            topic (str, optional): The topic for APNS notifications.
            environment (PNPushEnvironment, optional): The environment for APNS.

        Returns:
            RemoveDeviceFromPush: A RemoveDeviceFromPush object that can be used
            to execute the request.

        Example:
            ```python
            pubnub.remove_device_from_push(
                device_id="device_token",
                push_type=PNPushType.FCM
            ).sync()
            ```
        """
        return RemoveDeviceFromPush(self, device_id=device_id, push_type=push_type, topic=topic,
                                    environment=environment)

    def history(self) -> History:
        """Fetch historical messages from a channel.

        Retrieves previously published messages from the PubNub network.

        Returns:
            History: A History object that can be used to configure and execute the request.

        Example:
            ```python
            result = pubnub.history()\
                .channel("chat")\
                .count(100)\
                .include_timetoken(True)\
                .sync()

            for message in result.messages:
                print(f"Message: {message.entry} at {message.timetoken}")
            ```

        Note:
            The number of messages that can be retrieved is limited by your
            PubNub subscription level and message retention settings.
        """
        return History(self)

    def message_counts(self, channels: Union[str, List[str]] = None,
                       channels_timetoken: Union[str, List[str]] = None) -> MessageCount:
        """Get message counts for channels.

        Retrieves the number of messages published to specified channels,
        optionally filtered by timetoken.

        Args:
            channels: Channel(s) to get message counts for.
            channels_timetoken: Timetoken(s) to count messages from.

        Returns:
            MessageCount: A MessageCount object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.message_counts(
                channels=["chat", "alerts"],
                channels_timetoken=["15790288836087530"]
            ).sync()
            print(f"Messages in chat: {result.channels['chat']}")
            ```
        """
        return MessageCount(self, channels=channels, channels_timetoken=channels_timetoken)

    def fire(self, channel: str = None, message: Any = None, use_post: Optional[bool] = None,
             meta: Optional[Any] = None) -> Fire:
        return Fire(self, channel=channel, message=message, use_post=use_post, meta=meta)

    def signal(self, channel: str = None, message: Any = None, custom_message_type: Optional[str] = None) -> Signal:
        return Signal(self, channel=channel, message=message, custom_message_type=custom_message_type)

    def set_uuid_metadata(self, uuid: str = None, include_custom: bool = None, custom: dict = None,
                          include_status: bool = True, include_type: bool = True, status: str = None, type: str = None,
                          name: str = None, email: str = None, external_id: str = None,
                          profile_url: str = None) -> SetUuid:
        """Set or update metadata for a UUID.

        Associates custom metadata with a UUID that can be used for user profiles,
        presence information, or any other user-related data.

        Args:
            uuid (str, optional): The UUID to set metadata for.
            include_custom (bool, optional): Whether to include custom fields in response.
            custom (dict, optional): Custom metadata fields to set.
            include_status (bool, optional): Whether to include status in response.
            include_type (bool, optional): Whether to include type in response.
            status (str, optional): User's status (e.g., "online", "offline").
            type (str, optional): User's type or role.
            name (str, optional): User's display name.
            email (str, optional): User's email address.
            external_id (str, optional): External system identifier.
            profile_url (str, optional): URL to user's profile image.

        Returns:
            SetUuid: A SetUuid object that can be used to execute the request.

        Example:
            ```python
            pubnub.set_uuid_metadata() \
                .uuid("user-123") \
                .name("John Doe") \
                .email("john@example.com") \
                .custom({"role": "admin"}) \
                .sync()
            ```
        """
        return SetUuid(self, uuid=uuid, include_custom=include_custom, custom=custom, include_status=include_status,
                       include_type=include_type, status=status, type=type, name=name, email=email,
                       external_id=external_id, profile_url=profile_url)

    def get_uuid_metadata(self, uuid: str = None, include_custom: bool = None, include_status: bool = True,
                          include_type: bool = True) -> GetUuid:
        """Get metadata for a specific UUID.

        Retrieves the metadata associated with a UUID including custom fields,
        status, and type information.

        Args:
            uuid (str, optional): The UUID to get metadata for.
            include_custom (bool, optional): Whether to include custom fields.
            include_status (bool, optional): Whether to include status.
            include_type (bool, optional): Whether to include type.

        Returns:
            GetUuid: A GetUuid object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.get_uuid_metadata()\
                .uuid("user-123")\
                .include_custom(True)\
                .sync()
            print(f"User name: {result.result.data['name']}")
            ```
        """
        return GetUuid(self, uuid=uuid, include_custom=include_custom, include_status=include_status,
                       include_type=include_type)

    def remove_uuid_metadata(self, uuid: str = None) -> RemoveUuid:
        """Remove all metadata for a UUID.

        Deletes all metadata associated with a UUID including custom fields,
        status, and type information.

        Args:
            uuid (str, optional): The UUID to remove metadata for.

        Returns:
            RemoveUuid: A RemoveUuid object that can be used to execute the request.

        Example:
            ```python
            pubnub.remove_uuid_metadata().uuid("user-123").sync()
            ```

        Warning:
            This operation is permanent and cannot be undone.
        """
        return RemoveUuid(self, uuid=uuid)

    def get_all_uuid_metadata(self, include_custom: bool = None, include_status: bool = True, include_type: bool = True,
                              limit: int = None, filter: str = None, include_total_count: bool = None,
                              sort_keys: list = None) -> GetAllUuid:
        """Get metadata for all UUIDs.

        Retrieves metadata for all UUIDs with optional filtering and sorting.

        Args:
            include_custom (bool, optional): Whether to include custom fields.
            include_status (bool, optional): Whether to include status.
            include_type (bool, optional): Whether to include type.
            limit (int, optional): Maximum number of results to return.
            filter (str, optional): Filter expression for results.
            include_total_count (bool, optional): Whether to include total count.
            sort_keys (list, optional): Keys to sort results by.

        Returns:
            GetAllUuid: A GetAllUuid object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.get_all_uuid_metadata()\
                .include_custom(True)\
                .filter("name LIKE 'John*'")\
                .limit(100)\
                .sync()
            for user in result.result.data:
                print(f"User: {user['name']}")
            ```
        """
        return GetAllUuid(self, include_custom=include_custom, include_status=include_status, include_type=include_type,
                          limit=limit, filter=filter, include_total_count=include_total_count, sort_keys=sort_keys)

    def set_channel_metadata(self, channel: str = None, custom: dict = None, include_custom: bool = False,
                             include_status: bool = True, include_type: bool = True, name: str = None,
                             description: str = None, status: str = None, type: str = None) -> SetChannel:
        """Set or update metadata for a channel.

        Associates custom metadata with a channel that can be used for channel
        information, categorization, or any other channel-related data.

        Args:
            channel (str, optional): The channel to set metadata for.
            custom (dict, optional): Custom metadata fields to set.
            include_custom (bool, optional): Whether to include custom fields in response.
            include_status (bool, optional): Whether to include status in response.
            include_type (bool, optional): Whether to include type in response.
            name (str, optional): Display name for the channel.
            description (str, optional): Channel description.
            status (str, optional): Channel status (e.g., "active", "archived").
            type (str, optional): Channel type or category.

        Returns:
            SetChannel: A SetChannel object that can be used to execute the request.

        Example:
            ```python
            pubnub.set_channel_metadata()\
                .channel("room-1")\
                .name("General Chat")\
                .description("Public chat room for general discussions")\
                .custom({"category": "public"})\
                .sync()
            ```
        """
        return SetChannel(self, channel=channel, custom=custom, include_custom=include_custom,
                          include_status=include_status, include_type=include_type, name=name, description=description,
                          status=status, type=type)

    def get_channel_metadata(self, channel: str = None, include_custom: bool = False, include_status: bool = True,
                             include_type: bool = True) -> GetChannel:
        """Get metadata for a specific channel.

        Retrieves the metadata associated with a channel including custom fields,
        status, and type information.

        Args:
            channel (str, optional): The channel to get metadata for.
            include_custom (bool, optional): Whether to include custom fields.
            include_status (bool, optional): Whether to include status.
            include_type (bool, optional): Whether to include type.

        Returns:
            GetChannel: A GetChannel object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.get_channel_metadata()\
                .channel("room-1")\
                .include_custom(True)\
                .sync()
            print(f"Channel name: {result.result.data['name']}")
            ```
        """
        return GetChannel(self, channel=channel, include_custom=include_custom, include_status=include_status,
                          include_type=include_type)

    def remove_channel_metadata(self, channel: str = None) -> RemoveChannel:
        """Remove all metadata for a channel.

        Deletes all metadata associated with a channel including custom fields,
        status, and type information.

        Args:
            channel (str, optional): The channel to remove metadata for.

        Returns:
            RemoveChannel: A RemoveChannel object that can be used to execute the request.

        Example:
            ```python
            pubnub.remove_channel_metadata().channel("room-1").sync()
            ```

        Warning:
            This operation is permanent and cannot be undone.
        """
        return RemoveChannel(self, channel=channel)

    def get_all_channel_metadata(self, include_custom=False, include_status=True, include_type=True,
                                 limit: int = None, filter: str = None, include_total_count: bool = None,
                                 sort_keys: list = None, page: PNPage = None) -> GetAllChannels:
        """Get metadata for all channels.

        Retrieves metadata for all channels with optional filtering and sorting.

        Args:
            include_custom (bool, optional): Whether to include custom fields.
            include_status (bool, optional): Whether to include status.
            include_type (bool, optional): Whether to include type.
            limit (int, optional): Maximum number of results to return.
            filter (str, optional): Filter expression for results.
            include_total_count (bool, optional): Whether to include total count.
            sort_keys (list, optional): Keys to sort results by.
            page (PNPage, optional): Pagination information.

        Returns:
            GetAllChannels: A GetAllChannels object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.get_all_channel_metadata()\
                .include_custom(True)\
                .filter("name LIKE 'chat*'")\
                .limit(100)\
                .sync()
            for channel in result.result.data:
                print(f"Channel: {channel['name']}")
            ```
        """
        return GetAllChannels(self, include_custom=include_custom, include_status=include_status,
                              include_type=include_type, limit=limit, filter=filter,
                              include_total_count=include_total_count, sort_keys=sort_keys, page=page)

    def set_channel_members(self, channel: str = None, uuids: List[PNUUID] = None, include_custom: bool = None,
                            limit: int = None, filter: str = None, include_total_count: bool = None,
                            sort_keys: list = None, page: PNPage = None, include: MemberIncludes = None
                            ) -> SetChannelMembers:
        """Set the members (UUIDs) of a channel, replacing any existing members.

        This method allows you to set the complete list of members for a channel,
        overwriting any existing members. This is useful when you want to completely
        replace the current member list rather than add or remove individual members.

        Args:
            channel (str, optional): The channel to set members for.
            uuids (List[PNUUID], optional): List of UUIDs to set as channel members.
            include_custom (bool, optional): Whether to include custom fields in response.
            limit (int, optional): Maximum number of results to return.
            filter (str, optional): Expression to filter results.
            include_total_count (bool, optional): Whether to include total count in response.
            sort_keys (list, optional): Keys to sort results by.
            page (PNPage, optional): Pagination parameters.
            include (MemberIncludes, optional): Additional fields to include in response.

        Returns:
            SetChannelMembers: A SetChannelMembers object that can be used to execute the request.

        Example:
            ```python
            pubnub.set_channel_members()\
                .channel("room-1")\
                .uuids([PNUser("user-1"), PNUser("user-2"), PNUser("user-3")])\
                .sync()
            ```
        """
        return SetChannelMembers(self, channel=channel, uuids=uuids, include_custom=include_custom, limit=limit,
                                 filter=filter, include_total_count=include_total_count, sort_keys=sort_keys,
                                 page=page, include=include)

    def get_channel_members(self, channel: str = None, include_custom: bool = None, limit: int = None,
                            filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                            page: PNPage = None, include: MemberIncludes = None) -> GetChannelMembers:
        """Retrieve a list of members (UUIDs) that are part of a channel.

        This method allows you to fetch all members currently associated with a channel,
        with options for pagination and including additional information.

        Args:
            channel (str, optional): The channel to get members from.
            include_custom (bool, optional): Whether to include custom fields in response.
            limit (int, optional): Maximum number of results to return.
            filter (str, optional): Expression to filter results.
            include_total_count (bool, optional): Whether to include total count in response.
            sort_keys (list, optional): Keys to sort results by.
            page (PNPage, optional): Pagination parameters.
            include (MemberIncludes, optional): Additional fields to include in response.

        Returns:
            GetChannelMembers: A GetChannelMembers object that can be used to execute the request.

        Example:
            ```python
            pubnub.get_channel_members()\
                .channel("room-1")\
                .include_custom(True)\
                .sync()
            ```
        """
        return GetChannelMembers(self, channel=channel, include_custom=include_custom, limit=limit, filter=filter,
                                 include_total_count=include_total_count, sort_keys=sort_keys, page=page,
                                 include=include)

    def remove_channel_members(self, channel: str = None, uuids: List[str] = None, include_custom: bool = None,
                               limit: int = None, filter: str = None, include_total_count: bool = None,
                               sort_keys: list = None, page: PNPage = None, include: MemberIncludes = None
                               ) -> RemoveChannelMembers:
        """Remove members (UUIDs) from a channel.

        This method allows you to remove one or more members from a channel in a single operation.

        Args:
            channel (str, optional): The channel to remove members from.
            uuids (List[str], optional): List of UUIDs to remove from the channel.
            include_custom (bool, optional): Whether to include custom fields in response.
            limit (int, optional): Maximum number of results to return.
            filter (str, optional): Expression to filter results.
            include_total_count (bool, optional): Whether to include total count in response.
            sort_keys (list, optional): Keys to sort results by.
            page (PNPage, optional): Pagination parameters.
            include (MemberIncludes, optional): Additional fields to include in response.

        Returns:
            RemoveChannelMembers: A RemoveChannelMembers object that can be used to execute the request.

        Example:
            ```python
            pubnub.remove_channel_members()\
                .channel("room-1")\
                .uuids(["user-1", "user-2"])\
                .sync()
            ```
        """
        return RemoveChannelMembers(self, channel=channel, uuids=uuids, include_custom=include_custom, limit=limit,
                                    filter=filter, include_total_count=include_total_count, sort_keys=sort_keys,
                                    page=page, include=include)

    def manage_channel_members(self, channel: str = None, uuids_to_set: List[str] = None,
                               uuids_to_remove: List[str] = None, include_custom: bool = None, limit: int = None,
                               filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                               page: PNPage = None, include: MemberIncludes = None) -> ManageChannelMembers:
        """Manage members of a channel by adding and/or removing UUIDs.

        This method allows you to add new members to a channel and remove existing members
        in a single operation.

        Args:
            channel (str, optional): The channel to manage members for.
            uuids_to_set (List[str], optional): List of UUIDs to add as members.
            uuids_to_remove (List[str], optional): List of UUIDs to remove from members.
            include_custom (bool, optional): Whether to include custom fields in response.
            limit (int, optional): Maximum number of results to return.
            filter (str, optional): Expression to filter results.
            include_total_count (bool, optional): Whether to include total count in response.
            sort_keys (list, optional): Keys to sort results by.
            page (PNPage, optional): Pagination parameters.
            include (MemberIncludes, optional): Additional fields to include in response.

        Returns:
            ManageChannelMembers: A ManageChannelMembers object that can be used to execute the request.

        Example:
            ```python
            pubnub.manage_channel_members()\
                .channel("room-1")\
                .uuids_to_set(["user-1", "user-2"])\
                .uuids_to_remove(["user-3"])\
                .sync()
            ```
        """
        return ManageChannelMembers(self, channel=channel, uuids_to_set=uuids_to_set, uuids_to_remove=uuids_to_remove,
                                    include_custom=include_custom, limit=limit, filter=filter,
                                    include_total_count=include_total_count, sort_keys=sort_keys, page=page,
                                    include=include)

    def set_memberships(self, uuid: str = None, channel_memberships: List[str] = None, include_custom: bool = False,
                        limit: int = None, filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                        page: PNPage = None, include: MembershipIncludes = None) -> SetMemberships:
        """Set channel memberships for a UUID.

        This method allows you to set the channels that a UUID is a member of,
        replacing any existing memberships.

        Args:
            uuid (str, optional): The UUID to set memberships for.
            channel_memberships (List[str], optional): List of channels to set as memberships.
            include_custom (bool, optional): Whether to include custom fields in response.
            limit (int, optional): Maximum number of results to return.
            filter (str, optional): Expression to filter results.
            include_total_count (bool, optional): Whether to include total count in response.
            sort_keys (list, optional): Keys to sort results by.
            page (PNPage, optional): Pagination parameters.
            include (MembershipIncludes, optional): Additional fields to include in response.

        Returns:
            SetMemberships: A SetMemberships object that can be used to execute the request.

        Example:
            ```python
            pubnub.set_memberships()\
                .uuid("user-1")\
                .channel_memberships(["room-1", "room-2"])\
                .sync()
            ```
        """
        return SetMemberships(self, uuid=uuid, channel_memberships=channel_memberships, include_custom=include_custom,
                              limit=limit, filter=filter, include_total_count=include_total_count, sort_keys=sort_keys,
                              page=page, include=include)

    def get_memberships(self, uuid: str = None, include_custom: bool = False, limit: int = None, filter: str = None,
                        include_total_count: bool = None, sort_keys: list = None, page: PNPage = None,
                        include: MembershipIncludes = None):
        """Get channel memberships for a UUID.

        Retrieves a list of channels that a UUID is a member of.

        Args:
            uuid (str, optional): The UUID to get memberships for.
            include_custom (bool, optional): Whether to include custom fields in response.
            limit (int, optional): Maximum number of results to return.
            filter (str, optional): Expression to filter results.
            include_total_count (bool, optional): Whether to include total count in response.
            sort_keys (list, optional): Keys to sort results by.
            page (PNPage, optional): Pagination parameters.
            include (MembershipIncludes, optional): Additional fields to include in response.

        Returns:
            GetMemberships: A GetMemberships object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.get_memberships()\
                .uuid("user-1")\
                .include_custom(True)\
                .sync()
            for membership in result.data:
                print(f"Channel: {membership['channel']}")
            ```
        """
        return GetMemberships(self, uuid=uuid, include_custom=include_custom, limit=limit, filter=filter,
                              include_total_count=include_total_count, sort_keys=sort_keys, page=page, include=include)

    def manage_memberships(self, uuid: str = None, channel_memberships_to_set: List[str] = None,
                           channel_memberships_to_remove: List[str] = None, include_custom: bool = False,
                           limit: int = None, filter: str = None, include_total_count: bool = None,
                           sort_keys: list = None, page: PNPage = None, include: MembershipIncludes = None
                           ) -> ManageMemberships:
        """Manage channel memberships for a UUID by adding and/or removing channels.

        This method allows you to add new channel memberships and remove existing ones
        for a UUID in a single operation.

        Args:
            uuid (str, optional): The UUID to manage memberships for.
            channel_memberships_to_set (List[str], optional): List of channels to add as memberships.
            channel_memberships_to_remove (List[str], optional): List of channels to remove from memberships.
            include_custom (bool, optional): Whether to include custom fields in response.
            limit (int, optional): Maximum number of results to return.
            filter (str, optional): Expression to filter results.
            include_total_count (bool, optional): Whether to include total count in response.
            sort_keys (list, optional): Keys to sort results by.
            page (PNPage, optional): Pagination parameters.
            include (MembershipIncludes, optional): Additional fields to include in response.

        Returns:
            ManageMemberships: A ManageMemberships object that can be used to execute the request.

        Example:
            ```python
            pubnub.manage_memberships()\
                .uuid("user-1")\
                .channel_memberships_to_set(["room-1", "room-2"])\
                .channel_memberships_to_remove(["room-3"])\
                .sync()
            ```
        """
        return ManageMemberships(self, uuid=uuid, channel_memberships_to_set=channel_memberships_to_set,
                                 channel_memberships_to_remove=channel_memberships_to_remove,
                                 include_custom=include_custom, limit=limit, filter=filter,
                                 include_total_count=include_total_count, sort_keys=sort_keys, page=page,
                                 include=include)

    def fetch_messages(self, channels: Union[str, List[str]] = None, start: Optional[int] = None,
                       end: Optional[int] = None, count: Optional[int] = None,
                       include_meta: Optional[bool] = None, include_message_actions: Optional[bool] = None,
                       include_message_type: Optional[bool] = None, include_uuid: Optional[bool] = None,
                       decrypt_messages: bool = False) -> FetchMessages:
        return FetchMessages(self, channels=channels, start=start, end=end, count=count, include_meta=include_meta,
                             include_message_actions=include_message_actions, include_message_type=include_message_type,
                             include_uuid=include_uuid, decrypt_messages=decrypt_messages)

    def add_message_action(self, channel: str = None, message_action: PNMessageAction = None) -> AddMessageAction:
        """Add an action to a message.

        Adds metadata like reactions, replies, or custom actions to an existing message.

        Args:
            channel (str, optional): The channel containing the message.
            message_action (PNMessageAction, optional): The action to add to the message.
                Should include type, value, and message timetoken.

        Returns:
            AddMessageAction: An AddMessageAction object that can be used to execute the request.

        Example:
            ```python
            from pubnub.models.consumer.message_actions import PNMessageAction

            action = PNMessageAction(
                type="reaction",
                value="👍",
                message_timetoken="1234567890"
            )
            pubnub.add_message_action(
                channel="chat",
                message_action=action
            ).sync()
            ```
        """
        return AddMessageAction(self, channel=channel, message_action=message_action)

    def get_message_actions(self, channel: str = None, start: Optional[str] = None,
                            end: Optional[str] = None, limit: Optional[str] = None) -> GetMessageActions:
        """Retrieve message actions for a channel.

        Gets a list of actions that have been added to messages in the specified channel.

        Args:
            channel (str, optional): The channel to get message actions from.
            start (str, optional): Start timetoken for the action search.
            end (str, optional): End timetoken for the action search.
            limit (str, optional): Maximum number of actions to return.

        Returns:
            GetMessageActions: A GetMessageActions object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.get_message_actions(
                channel="chat",
                limit="10"
            ).sync()
            for action in result.actions:
                print(f"Action: {action.type} - {action.value}")
            ```
        """
        return GetMessageActions(self, channel=channel, start=start, end=end, limit=limit)

    def remove_message_action(self, channel: str = None, message_timetoken: Optional[int] = None,
                              action_timetoken: Optional[int] = None) -> RemoveMessageAction:
        """Remove an action from a message.

        Deletes a specific action that was previously added to a message.

        Args:
            channel (str, optional): The channel containing the message.
            message_timetoken (int, optional): Timetoken of the original message.
            action_timetoken (int, optional): Timetoken of the action to remove.

        Returns:
            RemoveMessageAction: A RemoveMessageAction object that can be used to execute the request.

        Example:
            ```python
            pubnub.remove_message_action(
                channel="chat",
                message_timetoken=1234567890,
                action_timetoken=1234567891
            ).sync()
            ```
        """
        return RemoveMessageAction(self, channel=channel, message_timetoken=message_timetoken,
                                   action_timetoken=action_timetoken)

    def time(self) -> Time:
        return Time(self)

    def delete_messages(self, channel: str = None, start: Optional[int] = None,
                        end: Optional[int] = None) -> HistoryDelete:
        """Delete messages from a channel's history.

        Permanently removes messages from a channel within the specified timeframe.

        Args:
            channel (str, optional): The channel to delete messages from.
            start (int, optional): Start timetoken for deletion range.
            end (int, optional): End timetoken for deletion range.

        Returns:
            HistoryDelete: A HistoryDelete object that can be used to execute the request.

        Example:
            ```python
            pubnub.delete_messages(
                channel="chat",
                start=15790288836087530,
                end=15790288836087540
            ).sync()
            ```

        Warning:
            This operation is permanent and cannot be undone. Use with caution.
        """
        return HistoryDelete(self, channel=channel, start=start, end=end)

    def parse_token(self, token: str) -> Any:
        """Parse an access token to examine its contents.

        Args:
            token (str): The token string to parse.

        Returns:
            Any: The parsed token data structure.

        Example:
            ```python
            token_data = pubnub.parse_token("my-token-string")
            print(f"Token permissions: {token_data.permissions}")
            ```
        """
        return self._token_manager.parse_token(token)

    def set_token(self, token: str) -> None:
        """Set the access token for this PubNub instance.

        Args:
            token (str): The token string to use for authentication.

        Note:
            This token will be used for all subsequent requests that
            require authentication.
        """
        self._token_manager.set_token(token)

    def _get_token(self) -> Optional[str]:
        """Get the current access token.

        Returns:
            Optional[str]: The current token string, or None if not set.

        Note:
            This is an internal method used by the SDK for authentication.
        """
        return self._token_manager.get_token()

    def send_file(self) -> Union['SendFileNative', 'AsyncioSendFile']:
        """Send a file through PubNub's file upload service.

        The method automatically selects the appropriate implementation based on
        the SDK platform (synchronous or asynchronous).

        Returns:
            Union[SendFileNative, AsyncioSendFile]: A file sender object that can
            be used to configure and execute the file upload.

        Raises:
            NotImplementedError: If the SDK platform is not supported.

        Example:
            ```python
            with open("image.jpg", "rb") as file:
                pubnub.send_file() \
                    .channel("room-1") \
                    .file_name("image.jpg") \
                    .file_object(file) \
                    .message("My dog is a good boy") \
                    .sync()
            ```
        """
        if not self.sdk_platform():
            return SendFileNative(self)
        elif "Asyncio" in self.sdk_platform():
            from pubnub.endpoints.file_operations.send_file_asyncio import AsyncioSendFile
            return AsyncioSendFile(self)
        else:
            raise NotImplementedError

    def download_file(self) -> Union['DownloadFileNative', 'DownloadFileAsyncio']:
        """Download a file from PubNub's file storage service.

        The method automatically selects the appropriate implementation based on
        the SDK platform (synchronous or asynchronous).

        Returns:
            Union[DownloadFileNative, DownloadFileAsyncio]: A file downloader object
            that can be used to configure and execute the file download.

        Raises:
            NotImplementedError: If the SDK platform is not supported.

        Example:
            ```python
            pubnub.download_file()\
                .channel("room-1")\
                .file_id("abc123") \
                .file_name("image.jpg") \
                .sync()
            ```
        """
        if not self.sdk_platform():
            return DownloadFileNative(self)
        elif "Asyncio" in self.sdk_platform():
            from pubnub.endpoints.file_operations.download_file_asyncio import DownloadFileAsyncio
            return DownloadFileAsyncio(self)
        else:
            raise NotImplementedError

    def list_files(self, channel: str = None, *, limit: int = None, next: str = None) -> ListFiles:
        """List files stored in a channel.

        Retrieves metadata about files that have been uploaded to a specific channel.

        Args:
            channel (str, optional): The channel to list files from.
            limit (int, optional): The maximum number of files to return.
            next (str, optional): The pagination token for the next page of results.

        Returns:
            ListFiles: A ListFiles object that can be used to execute the request.

        Example:
            ```python
            result = pubnub.list_files(channel="room-1", limit=10, next="next_token").sync()
            for file in result.data:
                print(f"File: {file.name}, Size: {file.size}")
            ```
        """
        return ListFiles(self, channel=channel, limit=limit, next=next)

    def get_file_url(self, channel: str = None, file_name: str = None, file_id: str = None) -> GetFileDownloadUrl:
        """Get the download URL for a specific file.

        Generates a temporary URL that can be used to download a file.

        Args:
            channel (str, optional): The channel where the file is stored.
            file_name (str, optional): The name of the file.
            file_id (str, optional): The unique identifier of the file.

        Returns:
            GetFileDownloadUrl: A GetFileDownloadUrl object that can be used to execute the request.

        Example:
            ```python
            url = pubnub.get_file_url(
                channel="room-1",
                file_id="abc123",
                file_name="image.jpg"
            ).sync()
            ```
        """
        return GetFileDownloadUrl(self, channel=channel, file_name=file_name, file_id=file_id)

    def delete_file(self, channel: str = None, file_name: str = None, file_id: str = None) -> DeleteFile:
        """Delete a file from PubNub's file storage.

        Permanently removes a file from the specified channel.

        Args:
            channel (str, optional): The channel where the file is stored.
            file_name (str, optional): The name of the file to delete.
            file_id (str, optional): The unique identifier of the file to delete.

        Returns:
            DeleteFile: A DeleteFile object that can be used to execute the request.

        Example:
            ```python
            pubnub.delete_file(
                channel="room-1",
                file_id="abc123",
                file_name="image.jpg"
            ).sync()
            ```
        """
        return DeleteFile(self, channel=channel, file_name=file_name, file_id=file_id)

    def _fetch_file_upload_s3_data(self) -> FetchFileUploadS3Data:
        return FetchFileUploadS3Data(self)

    def publish_file_message(self) -> PublishFileMessage:
        return PublishFileMessage(self)

    def decrypt(self, cipher_key: str, file: Any) -> Any:
        warn('Deprecated: Usage of decrypt with cipher key will be removed. Use PubNub.crypto.decrypt instead')
        return self.config.file_crypto.decrypt(cipher_key, file)

    def encrypt(self, cipher_key: str, file: Any) -> Any:
        warn('Deprecated: Usage of encrypt with cipher key will be removed. Use PubNub.crypto.encrypt instead')
        return self.config.file_crypto.encrypt(cipher_key, file)

    @staticmethod
    def timestamp() -> int:
        """Get the current timestamp.

        Returns:
            int: Current Unix timestamp in seconds.

        Note:
            This method is used internally for generating request timestamps
            and can be used for custom timing needs.
        """
        return int(time.time())

    def _validate_subscribe_manager_enabled(self) -> None:
        if self._subscription_manager is None:
            raise Exception("Subscription manager is not enabled for this instance")

    """ Entities code -- all of methods bellow should be decorated with pubnub.features.feature_flag """
    @feature_flag('PN_ENABLE_ENTITIES')
    def create_space(
        self, space_id, name=None, description=None, custom=None, space_type=None, space_status=None, sync=None
    ):
        space = CreateSpace(self).space_id(space_id)

        if name is not None:
            space.set_name(name)

        if description is not None:
            space.description(description)

        if custom is not None:
            space.custom(custom)

        if space_status is not None:
            space.space_status(space_status)

        if space_type is not None:
            space.space_type(space_type)

        if sync:
            return space.sync()

        return space

    @feature_flag('PN_ENABLE_ENTITIES')
    def update_space(
        self, space_id, name=None, description=None, custom=None, space_type=None, space_status=None, sync=None
    ):
        space = UpdateSpace(self).space_id(space_id)

        if name is not None:
            space.set_name(name)

        if description is not None:
            space.description(description)

        if custom is not None:
            space.custom(custom)

        if space_status is not None:
            space.space_status(space_status)

        if space_type is not None:
            space.space_type(space_type)

        if sync:
            return space.sync()

        return space

    @feature_flag('PN_ENABLE_ENTITIES')
    def remove_space(self, space_id, sync=None):
        remove_space = RemoveSpace(self).space_id(space_id)

        if sync:
            return remove_space.sync()

        return remove_space

    @feature_flag('PN_ENABLE_ENTITIES')
    def fetch_space(self, space_id, include_custom=None, sync=None):
        space = FetchSpace(self).space_id(space_id)

        if include_custom is not None:
            space.include_custom(include_custom)

        if sync:
            return space.sync()
        return space

    @feature_flag('PN_ENABLE_ENTITIES')
    def fetch_spaces(self, limit=None, page=None, filter=None, sort=None, include_total_count=None, include_custom=None,
                     sync=None):

        spaces = FetchSpaces(self)

        if limit is not None:
            spaces.limit(limit)

        if page is not None:
            spaces.page(page)

        if filter is not None:
            spaces.filter(filter)

        if sort is not None:
            spaces.sort(sort)

        if include_total_count is not None:
            spaces.include_total_count(include_total_count)

        if include_custom is not None:
            spaces.include_custom(include_custom)

        if sync:
            return spaces.sync()
        return spaces

    @feature_flag('PN_ENABLE_ENTITIES')
    def create_user(self, user_id, name=None, email=None, custom=None, user_type=None, user_status=None, sync=None):
        user = CreateUser(self).user_id(user_id)

        if name is not None:
            user.set_name(name)

        if email is not None:
            user.email(email)

        if custom is not None:
            user.custom(custom)

        if user_status is not None:
            user.user_status(user_status)

        if user_type is not None:
            user.user_type(user_type)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def update_user(self, user_id, name=None, email=None, custom=None, user_type=None, user_status=None, sync=None):
        user = UpdateUser(self).user_id(user_id)

        if name is not None:
            user.set_name(name)

        if email is not None:
            user.email(email)

        if custom is not None:
            user.custom(custom)

        if user_status is not None:
            user.user_status(user_status)

        if user_type is not None:
            user.user_type(user_type)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def remove_user(self, user_id, sync=None):
        user = RemoveUser(self).user_id(user_id)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def fetch_user(self, user_id, include_custom=None, sync=None):
        user = FetchUser(self).user_id(user_id)

        if include_custom is not None:
            user.include_custom(include_custom)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def fetch_users(self, limit=None, page=None, filter=None, sort=None, include_total_count=None, include_custom=None,
                    sync=None):
        users = FetchUsers(self)

        if limit is not None:
            users.limit(limit)

        if page is not None:
            users.page(page)

        if filter is not None:
            users.filter(filter)

        if sort is not None:
            users.sort(sort)

        if include_total_count is not None:
            users.include_total_count(include_total_count)

        if include_custom is not None:
            users.include_custom(include_custom)

        if sync:
            return users.sync()
        return users

    @feature_flag('PN_ENABLE_ENTITIES')
    def add_memberships(
        self,
        user_id: str = None,
        users: list = None,
        space_id: str = None,
        spaces: list = None,
        sync=None
    ):
        if user_id and space_id:
            raise (PubNubException(pn_error=PNERR_MISUSE_OF_USER_AND_SPACE))
        if user_id and spaces:
            membership = AddUserSpaces(self).user_id(user_id).spaces(spaces)
        elif space_id and users:
            membership = AddSpaceMembers(self).space_id(space_id).users(users)
        else:
            raise (PubNubException(pn_error=PNERR_USER_SPACE_PAIRS_MISSING))

        if sync:
            return membership.sync()
        return membership

    @feature_flag('PN_ENABLE_ENTITIES')
    def update_memberships(
        self,
        user_id: str = None,
        users: list = None,
        space_id: str = None,
        spaces: list = None,
        sync=None
    ):
        if user_id and space_id:
            raise (PubNubException(pn_error=PNERR_MISUSE_OF_USER_AND_SPACE))
        if user_id and spaces:
            membership = UpdateUserSpaces(self).user_id(user_id).spaces(spaces)
        elif space_id and users:
            membership = UpdateSpaceMembers(self).space_id(space_id).users(users)
        else:
            raise (PubNubException(pn_error=PNERR_USER_SPACE_PAIRS_MISSING))

        if sync:
            return membership.sync()
        return membership

    def remove_memberships(self, **kwargs):
        if len(kwargs) == 0 or ('user_id' not in kwargs.keys() and 'space_id' not in kwargs.keys()):
            return RemoveMemberships(self, **kwargs)

        if 'user_id' in kwargs.keys() and 'space_id' in kwargs.keys():
            raise (PubNubException(pn_error=PNERR_MISUSE_OF_USER_AND_SPACE))

        if 'user_id' in kwargs.keys() and 'spaces' in kwargs.keys():
            membership = RemoveUserSpaces(self).user_id(kwargs['user_id']).spaces(kwargs['spaces'])
        elif 'space_id' in kwargs.keys() and 'users' in kwargs.keys():
            membership = RemoveSpaceMembers(self).space_id(kwargs['space_id']).users(kwargs['users'])
        else:
            raise (PubNubException(pn_error=PNERR_USER_SPACE_PAIRS_MISSING))

        if kwargs['sync']:
            return membership.sync()
        return membership

    @feature_flag('PN_ENABLE_ENTITIES')
    def fetch_memberships(self, user_id: str = None, space_id: str = None, limit=None, page=None, filter=None,
                          sort=None, include_total_count=None, include_custom=None, sync=None):
        if user_id and space_id:
            raise (PubNubException(pn_error=PNERR_MISUSE_OF_USER_AND_SPACE))

        if user_id:
            memberships = FetchUserMemberships(self).user_id(user_id)
        elif space_id:
            memberships = FetchSpaceMemberships(self).space_id(space_id)
        else:
            raise (PubNubException(pn_error=PNERR_USER_SPACE_PAIRS_MISSING))

        if limit:
            memberships.limit(limit)

        if page:
            memberships.page(page)

        if filter:
            memberships.filter(filter)

        if sort:
            memberships.sort(sort)

        if include_total_count:
            memberships.include_total_count(include_total_count)

        if include_custom:
            memberships.include_custom(include_custom)

        if sync:
            return memberships.sync()
        return memberships

    def channel(self, channel: str) -> PubNubChannel:
        return PubNubChannel(self, channel)

    def channel_group(self, channel_group: str) -> PubNubChannelGroup:
        return PubNubChannelGroup(self, channel_group)

    def channel_metadata(self, channel: str) -> PubNubChannelMetadata:
        return PubNubChannelMetadata(self, channel)

    def user_metadata(self, user_id: str) -> PubNubUserMetadata:
        return PubNubUserMetadata(self, user_id)

    def subscription_set(self, subscriptions: list) -> PubNubSubscriptionSet:
        return PubNubSubscriptionSet(self, subscriptions)
