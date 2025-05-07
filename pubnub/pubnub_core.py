import logging
import time
from warnings import warn
from copy import deepcopy
from typing import Dict, List, Optional, Union
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

logger = logging.getLogger("pubnub")


class PubNubCore:
    """A base class for PubNub Python API implementations"""
    SDK_VERSION = "10.4.0"
    SDK_NAME = "PubNub-Python"

    TIMESTAMP_DIVIDER = 1000
    MAX_SEQUENCE = 65535

    __metaclass__ = ABCMeta
    __crypto = None

    _subscription_registry: PNSubscriptionRegistry

    def __init__(self, config: PNConfiguration):
        if not config.disable_config_locking:
            config.lock()
            self.config = deepcopy(config)
        else:
            self.config = config
        self.config.validate()
        self.headers = {
            'User-Agent': self.sdk_name
        }

        self._subscription_manager = None
        self._publish_sequence_manager = None
        self._telemetry_manager = TelemetryManager()
        self._base_path_manager = BasePathManager(config)
        self._token_manager = TokenManager()
        self._subscription_registry = PNSubscriptionRegistry(self)

    @property
    def base_origin(self):
        return self._base_path_manager.get_base_path()

    @property
    def sdk_name(self):
        return "%s%s/%s" % (PubNubCore.SDK_NAME, self.sdk_platform(), PubNubCore.SDK_VERSION)

    @abstractmethod
    def sdk_platform(self):
        pass

    @property
    def uuid(self):
        return self.config.uuid

    @property
    def crypto(self) -> PubNubCryptoModule:
        crypto_module = self.__crypto or self.config.crypto_module
        if not crypto_module and self.config.cipher_key:
            crypto_module = self.config.DEFAULT_CRYPTO_MODULE(self.config)
        return crypto_module

    @crypto.setter
    def crypto(self, crypto: PubNubCryptoModule):
        self.__crypto = crypto

    def add_listener(self, listener):
        self._validate_subscribe_manager_enabled()

        return self._subscription_manager.add_listener(listener)

    def remove_listener(self, listener):
        self._validate_subscribe_manager_enabled()

        return self._subscription_manager.remove_listener(listener)

    def get_subscribed_channels(self):
        self._validate_subscribe_manager_enabled()

        return self._subscription_manager.get_subscribed_channels()

    def get_subscribed_channel_groups(self):
        self._validate_subscribe_manager_enabled()
        return self._subscription_manager.get_subscribed_channel_groups()

    def add_channel_to_channel_group(self, channels: Union[str, List[str]] = None,
                                     channel_group: str = None) -> AddChannelToChannelGroup:
        return AddChannelToChannelGroup(self, channels=channels, channel_group=channel_group)

    def remove_channel_from_channel_group(self, channels: Union[str, List[str]] = None,
                                          channel_group: str = None) -> RemoveChannelFromChannelGroup:
        return RemoveChannelFromChannelGroup(self, channels=channels, channel_group=channel_group)

    def list_channels_in_channel_group(self, channel_group: str = None) -> ListChannelsInChannelGroup:
        return ListChannelsInChannelGroup(self, channel_group=channel_group)

    def remove_channel_group(self) -> RemoveChannelGroup:
        return RemoveChannelGroup(self)

    def subscribe(self) -> SubscribeBuilder:
        return SubscribeBuilder(self)

    def unsubscribe(self) -> UnsubscribeBuilder:
        return UnsubscribeBuilder(self)

    def unsubscribe_all(self):
        return self._subscription_registry.unsubscribe_all()

    def reconnect(self):
        return self._subscription_registry.reconnect()

    def heartbeat(self) -> Heartbeat:
        return Heartbeat(self)

    def set_state(self, channels: Union[str, List[str]] = None, channel_groups: Union[str, List[str]] = None,
                  state: Optional[Dict[str, any]] = None) -> SetState:
        return SetState(self, self._subscription_manager, channels, channel_groups, state)

    def get_state(self, channels: Union[str, List[str]] = None, channel_groups: Union[str, List[str]] = None,
                  uuid: Optional[str] = None) -> GetState:
        return GetState(self, channels, channel_groups, uuid)

    def here_now(self, channels: Union[str, List[str]] = None, channel_groups: Union[str, List[str]] = None,
                 include_state: bool = False, include_uuids: bool = True) -> HereNow:
        return HereNow(self, channels, channel_groups, include_state, include_uuids)

    def where_now(self, user_id: Optional[str] = None):
        return WhereNow(self, user_id)

    def publish(self, channel: str = None, message: any = None, should_store: Optional[bool] = None,
                use_post: Optional[bool] = None, meta: Optional[any] = None, replicate: Optional[bool] = None,
                ptto: Optional[int] = None, ttl: Optional[int] = None, custom_message_type: Optional[str] = None
                ) -> Publish:
        """ Sends a message to all channel subscribers. A successfully published message is replicated across PubNub's
        points of presence and sent simultaneously to all subscribed clients on a channel.
        """
        return Publish(self, channel=channel, message=message, should_store=should_store, use_post=use_post, meta=meta,
                       replicate=replicate, ptto=ptto, ttl=ttl, custom_message_type=custom_message_type)

    def grant(self):
        """ Deprecated. Use grant_token instead """
        warn("Access management v2 is being deprecated. We recommend switching to grant_token().",
             DeprecationWarning, stacklevel=2)
        return Grant(self)

    def grant_token(self, channels: Union[str, List[str]] = None, channel_groups: Union[str, List[str]] = None,
                    users: Union[str, List[str]] = None, spaces: Union[str, List[str]] = None,
                    authorized_user_id: str = None, ttl: Optional[int] = None, meta: Optional[any] = None):
        return GrantToken(self, channels=channels, channel_groups=channel_groups, users=users, spaces=spaces,
                          authorized_user_id=authorized_user_id, ttl=ttl, meta=meta)

    def revoke_token(self, token: str) -> RevokeToken:
        return RevokeToken(self, token)

    def audit(self):
        """ Deprecated """
        warn("Access management v2 is being deprecated.", DeprecationWarning, stacklevel=2)
        return Audit(self)

    # Push Related methods
    def list_push_channels(self, device_id: str = None, push_type: PNPushType = None, topic: str = None,
                           environment: PNPushEnvironment = None) -> ListPushProvisions:
        return ListPushProvisions(self, device_id=device_id, push_type=push_type, topic=topic, environment=environment)

    def add_channels_to_push(self, channels: Union[str, List[str]], device_id: str = None, push_type: PNPushType = None,
                             topic: str = None, environment: PNPushEnvironment = None) -> AddChannelsToPush:
        return AddChannelsToPush(self, channels=channels, device_id=device_id, push_type=push_type, topic=topic,
                                 environment=environment)

    def remove_channels_from_push(self, channels: Union[str, List[str]] = None, device_id: str = None,
                                  push_type: PNPushType = None, topic: str = None,
                                  environment: PNPushEnvironment = None) -> RemoveChannelsFromPush:
        return RemoveChannelsFromPush(self, channels=channels, device_id=device_id, push_type=push_type, topic=topic,
                                      environment=environment)

    def remove_device_from_push(self, device_id: str = None, push_type: PNPushType = None, topic: str = None,
                                environment: PNPushEnvironment = None) -> RemoveDeviceFromPush:
        return RemoveDeviceFromPush(self, device_id=device_id, push_type=push_type, topic=topic,
                                    environment=environment)

    def history(self):
        return History(self)

    def message_counts(self, channels: Union[str, List[str]] = None,
                       channels_timetoken: Union[str, List[str]] = None) -> MessageCount:
        return MessageCount(self, channels=channels, channels_timetoken=channels_timetoken)

    def fire(self, channel: str = None, message: any = None, use_post: Optional[bool] = None,
             meta: Optional[any] = None) -> Fire:
        return Fire(self, channel=channel, message=message, use_post=use_post, meta=meta)

    def signal(self, channel: str = None, message: any = None, custom_message_type: Optional[str] = None) -> Signal:
        return Signal(self, channel=channel, message=message, custom_message_type=custom_message_type)

    def set_uuid_metadata(self, uuid: str = None, include_custom: bool = None, custom: dict = None,
                          include_status: bool = True, include_type: bool = True, status: str = None, type: str = None,
                          name: str = None, email: str = None, external_id: str = None,
                          profile_url: str = None) -> SetUuid:
        return SetUuid(self, uuid=uuid, include_custom=include_custom, custom=custom, include_status=include_status,
                       include_type=include_type, status=status, type=type, name=name, email=email,
                       external_id=external_id, profile_url=profile_url)

    def get_uuid_metadata(self, uuid: str = None, include_custom: bool = None, include_status: bool = True,
                          include_type: bool = True) -> GetUuid:
        return GetUuid(self, uuid=uuid, include_custom=include_custom, include_status=include_status,
                       include_type=include_type)

    def remove_uuid_metadata(self, uuid: str = None) -> RemoveUuid:
        return RemoveUuid(self, uuid=uuid)

    def get_all_uuid_metadata(self, include_custom: bool = None, include_status: bool = True, include_type: bool = True,
                              limit: int = None, filter: str = None, include_total_count: bool = None,
                              sort_keys: list = None) -> GetAllUuid:
        return GetAllUuid(self, include_custom=include_custom, include_status=include_status, include_type=include_type,
                          limit=limit, filter=filter, include_total_count=include_total_count, sort_keys=sort_keys)

    def set_channel_metadata(self, channel: str = None, custom: dict = None, include_custom: bool = False,
                             include_status: bool = True, include_type: bool = True, name: str = None,
                             description: str = None, status: str = None, type: str = None) -> SetChannel:
        return SetChannel(self, channel=channel, custom=custom, include_custom=include_custom,
                          include_status=include_status, include_type=include_type, name=name, description=description,
                          status=status, type=type)

    def get_channel_metadata(self, channel: str = None, include_custom: bool = False, include_status: bool = True,
                             include_type: bool = True) -> GetChannel:
        return GetChannel(self, channel=channel, include_custom=include_custom, include_status=include_status,
                          include_type=include_type)

    def remove_channel_metadata(self, channel: str = None) -> RemoveChannel:
        return RemoveChannel(self, channel=channel)

    def get_all_channel_metadata(self, include_custom=False, include_status=True, include_type=True,
                                 limit: int = None, filter: str = None, include_total_count: bool = None,
                                 sort_keys: list = None, page: PNPage = None) -> GetAllChannels:
        return GetAllChannels(self, include_custom=include_custom, include_status=include_status,
                              include_type=include_type, limit=limit, filter=filter,
                              include_total_count=include_total_count, sort_keys=sort_keys, page=page)

    def set_channel_members(self, channel: str = None, uuids: List[PNUUID] = None, include_custom: bool = None,
                            limit: int = None, filter: str = None, include_total_count: bool = None,
                            sort_keys: list = None, page: PNPage = None, include: MemberIncludes = None
                            ) -> SetChannelMembers:
        """ Creates a builder for setting channel members. Can be used both as a builder or as a single call with
            named parameters.

            Parameters
            ----------
            channel : str
                The channel for which members are being set.
            uuids : List[PNUUID]
                List of users to be set as members of the channel.
            include_custom : bool, optional
                Whether to include custom fields in the response.
            limit : int, optional
                Maximum number of results to return.
            filter : str, optional
                Filter expression to apply to the results.
            include_total_count : bool, optional
                Whether to include the total count of results.
            sort_keys : list, optional
                List of keys to sort the results by.
            page : PNPage, optional
                Pagination information.
            include : MemberIncludes, optional
                Additional fields to include in the response.
            :return: An instance of SetChannelMembers builder.
            :rtype: SetChannelMembers

            Example:
            --------
                pn = PubNub(config)
                users = [PNUser("user1"), PNUser("user2", type="admin", status="offline")]
                response = pn.set_channel_members(channel="my_channel", uuids=users).sync()
        """
        return SetChannelMembers(self, channel=channel, uuids=uuids, include_custom=include_custom, limit=limit,
                                 filter=filter, include_total_count=include_total_count, sort_keys=sort_keys, page=page,
                                 include=include)

    def get_channel_members(self, channel: str = None, include_custom: bool = None, limit: int = None,
                            filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                            page: PNPage = None, include: MemberIncludes = None) -> GetChannelMembers:
        return GetChannelMembers(self, channel=channel, include_custom=include_custom, limit=limit, filter=filter,
                                 include_total_count=include_total_count, sort_keys=sort_keys, page=page,
                                 include=include)

    def remove_channel_members(self, channel: str = None, uuids: List[str] = None, include_custom: bool = None,
                               limit: int = None, filter: str = None, include_total_count: bool = None,
                               sort_keys: list = None, page: PNPage = None, include: MemberIncludes = None
                               ) -> RemoveChannelMembers:
        return RemoveChannelMembers(self, channel=channel, uuids=uuids, include_custom=include_custom, limit=limit,
                                    filter=filter, include_total_count=include_total_count, sort_keys=sort_keys,
                                    page=page, include=include)

    def manage_channel_members(self, channel: str = None, uuids_to_set: List[str] = None,
                               uuids_to_remove: List[str] = None, include_custom: bool = None, limit: int = None,
                               filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                               page: PNPage = None, include: MemberIncludes = None) -> ManageChannelMembers:
        return ManageChannelMembers(self, channel=channel, uuids_to_set=uuids_to_set, uuids_to_remove=uuids_to_remove,
                                    include_custom=include_custom, limit=limit, filter=filter,
                                    include_total_count=include_total_count, sort_keys=sort_keys, page=page,
                                    include=include)

    def set_memberships(self, uuid: str = None, channel_memberships: List[str] = None, include_custom: bool = False,
                        limit: int = None, filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                        page: PNPage = None, include: MembershipIncludes = None) -> SetMemberships:
        return SetMemberships(self, uuid=uuid, channel_memberships=channel_memberships, include_custom=include_custom,
                              limit=limit, filter=filter, include_total_count=include_total_count, sort_keys=sort_keys,
                              page=page, include=include)

    def get_memberships(self, uuid: str = None, include_custom: bool = False, limit: int = None, filter: str = None,
                        include_total_count: bool = None, sort_keys: list = None, page: PNPage = None,
                        include: MembershipIncludes = None):
        return GetMemberships(self, uuid=uuid, include_custom=include_custom, limit=limit, filter=filter,
                              include_total_count=include_total_count, sort_keys=sort_keys, page=page, include=include)

    def manage_memberships(self, uuid: str = None, channel_memberships_to_set: List[str] = None,
                           channel_memberships_to_remove: List[str] = None, include_custom: bool = False,
                           limit: int = None, filter: str = None, include_total_count: bool = None,
                           sort_keys: list = None, page: PNPage = None, include: MembershipIncludes = None
                           ) -> ManageMemberships:
        return ManageMemberships(self, uuid=uuid, channel_memberships_to_set=channel_memberships_to_set,
                                 channel_memberships_to_remove=channel_memberships_to_remove,
                                 include_custom=include_custom, limit=limit, filter=filter,
                                 include_total_count=include_total_count, sort_keys=sort_keys, page=page,
                                 include=include)

    def fetch_messages(self, channels: Union[str, List[str]] = None, start: int = None, end: int = None,
                       count: int = None, include_meta: bool = None, include_message_actions: bool = None,
                       include_message_type: bool = None, include_uuid: bool = None,
                       decrypt_messages: bool = False) -> FetchMessages:
        return FetchMessages(self, channels=channels, start=start, end=end, count=count, include_meta=include_meta,
                             include_message_actions=include_message_actions, include_message_type=include_message_type,
                             include_uuid=include_uuid, decrypt_messages=decrypt_messages)

    def add_message_action(self, channel: str = None, message_action: PNMessageAction = None):
        return AddMessageAction(self, channel=channel, message_action=message_action)

    def get_message_actions(self, channel: str = None, start: str = None, end: str = None,
                            limit: str = None) -> GetMessageActions:
        return GetMessageActions(self, channel=channel, start=start, end=end, limit=limit)

    def remove_message_action(self, channel: str = None, message_timetoken: int = None,
                              action_timetoken: int = None) -> RemoveMessageAction:
        return RemoveMessageAction(self, channel=channel, message_timetoken=message_timetoken,
                                   action_timetoken=action_timetoken)

    def time(self) -> Time:
        return Time(self)

    def delete_messages(self, channel: str = None, start: Optional[int] = None,
                        end: Optional[int] = None) -> HistoryDelete:
        return HistoryDelete(self, channel=channel, start=start, end=end)

    def parse_token(self, token):
        return self._token_manager.parse_token(token)

    def set_token(self, token):
        self._token_manager.set_token(token)

    def _get_token(self):
        return self._token_manager.get_token()

    def send_file(self):
        if not self.sdk_platform():
            return SendFileNative(self)
        elif "Asyncio" in self.sdk_platform():
            from pubnub.endpoints.file_operations.send_file_asyncio import AsyncioSendFile
            return AsyncioSendFile(self)
        else:
            raise NotImplementedError

    def download_file(self):
        if not self.sdk_platform():
            return DownloadFileNative(self)
        elif "Asyncio" in self.sdk_platform():
            from pubnub.endpoints.file_operations.download_file_asyncio import DownloadFileAsyncio
            return DownloadFileAsyncio(self)
        else:
            raise NotImplementedError

    def list_files(self, channel: str = None, *, limit: int = None, next: str = None) -> ListFiles:
        return ListFiles(self, channel=channel, limit=limit, next=next)

    def get_file_url(self, channel: str = None, file_name: str = None, file_id: str = None) -> GetFileDownloadUrl:
        return GetFileDownloadUrl(self, channel=channel, file_name=file_name, file_id=file_id)

    def delete_file(self, channel: str = None, file_name: str = None, file_id: str = None) -> DeleteFile:
        return DeleteFile(self, channel=channel, file_name=file_name, file_id=file_id)

    def _fetch_file_upload_s3_data(self) -> FetchFileUploadS3Data:
        return FetchFileUploadS3Data(self)

    def publish_file_message(self) -> PublishFileMessage:
        return PublishFileMessage(self)

    def decrypt(self, cipher_key, file):
        warn('Deprecated: Usage of decrypt with cipher key will be removed. Use PubNub.crypto.decrypt instead')
        return self.config.file_crypto.decrypt(cipher_key, file)

    def encrypt(self, cipher_key, file):
        warn('Deprecated: Usage of encrypt with cipher key will be removed. Use PubNub.crypto.encrypt instead')
        return self.config.file_crypto.encrypt(cipher_key, file)

    @staticmethod
    def timestamp():
        return int(time.time())

    def _validate_subscribe_manager_enabled(self):
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

    def channel(self, channel) -> PubNubChannel:
        return PubNubChannel(self, channel)

    def channel_group(self, channel_group) -> PubNubChannelGroup:
        return PubNubChannelGroup(self, channel_group)

    def channel_metadata(self, channel) -> PubNubChannelMetadata:
        return PubNubChannelMetadata(self, channel)

    def user_metadata(self, user_id) -> PubNubUserMetadata:
        return PubNubUserMetadata(self, user_id)

    def subscription_set(self, subscriptions: list) -> PubNubSubscriptionSet:
        return PubNubSubscriptionSet(self, subscriptions)
