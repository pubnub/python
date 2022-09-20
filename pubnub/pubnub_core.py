import logging
import time
from pubnub.endpoints.entities.membership.add_memberships import AddSpaceMembers, AddUserSpaces
from pubnub.endpoints.entities.membership.update_memberships import UpdateSpaceMembers, UpdateUserSpaces
from pubnub.endpoints.entities.membership.fetch_memberships import FetchSpaceMemberships, FetchUserMemberships
from pubnub.endpoints.entities.membership.remove_memberships import RemoveSpaceMembers, RemoveUserSpaces
from pubnub.endpoints.entities.user import CreateUser, FetchUser, FetchUsers, RemoveUser, UpdateUser, UpsertUser
from pubnub.endpoints.entities.space import CreateSpace, FetchSpace, FetchSpaces, RemoveSpace, UpdateSpace, UpsertSpace
from pubnub.errors import PNERR_MISUSE_OF_USER_AND_SPACE, PNERR_USER_SPACE_PAIRS_MISSING
from pubnub.exceptions import PubNubException
from pubnub.features import feature_flag

from abc import ABCMeta, abstractmethod

from .endpoints.objects_v2.uuid.set_uuid import SetUuid
from .endpoints.objects_v2.channel.get_all_channels import GetAllChannels
from .endpoints.objects_v2.channel.get_channel import GetChannel
from .endpoints.objects_v2.channel.remove_channel import RemoveChannel
from .endpoints.objects_v2.channel.set_channel import SetChannel
from .endpoints.objects_v2.members.get_channel_members import GetChannelMembers
from .endpoints.objects_v2.members.manage_channel_members import ManageChannelMembers
from .endpoints.objects_v2.members.remove_channel_members import RemoveChannelMembers
from .endpoints.objects_v2.members.set_channel_members import SetChannelMembers
from .endpoints.objects_v2.memberships.get_memberships import GetMemberships
from .endpoints.objects_v2.memberships.manage_memberships import ManageMemberships
from .endpoints.objects_v2.memberships.remove_memberships import RemoveMemberships
from .endpoints.objects_v2.memberships.set_memberships import SetMemberships
from .endpoints.objects_v2.uuid.get_all_uuid import GetAllUuid
from .endpoints.objects_v2.uuid.get_uuid import GetUuid
from .endpoints.objects_v2.uuid.remove_uuid import RemoveUuid
from .managers import BasePathManager, TokenManager
from .builders import SubscribeBuilder
from .builders import UnsubscribeBuilder
from .endpoints.time import Time
from .endpoints.history import History
from .endpoints.access.audit import Audit
from .endpoints.access.grant import Grant
from .endpoints.access.grant_token import GrantToken
from .endpoints.access.revoke_token import RevokeToken
from .endpoints.channel_groups.add_channel_to_channel_group import AddChannelToChannelGroup
from .endpoints.channel_groups.list_channels_in_channel_group import ListChannelsInChannelGroup
from .endpoints.channel_groups.remove_channel_from_channel_group import RemoveChannelFromChannelGroup
from .endpoints.channel_groups.remove_channel_group import RemoveChannelGroup
from .endpoints.presence.get_state import GetState
from .endpoints.presence.heartbeat import Heartbeat
from .endpoints.presence.set_state import SetState
from .endpoints.pubsub.publish import Publish
from .endpoints.pubsub.fire import Fire
from .endpoints.presence.here_now import HereNow
from .endpoints.presence.where_now import WhereNow
from .endpoints.history_delete import HistoryDelete
from .endpoints.message_count import MessageCount
from .endpoints.signal import Signal
from .endpoints.fetch_messages import FetchMessages
from .endpoints.message_actions.add_message_action import AddMessageAction
from .endpoints.message_actions.get_message_actions import GetMessageActions
from .endpoints.message_actions.remove_message_action import RemoveMessageAction
from .endpoints.file_operations.list_files import ListFiles
from .endpoints.file_operations.delete_file import DeleteFile
from .endpoints.file_operations.get_file_url import GetFileDownloadUrl
from .endpoints.file_operations.fetch_upload_details import FetchFileUploadS3Data
from .endpoints.file_operations.send_file import SendFileNative
from .endpoints.file_operations.download_file import DownloadFileNative
from .endpoints.file_operations.publish_file_message import PublishFileMessage

from .endpoints.push.add_channels_to_push import AddChannelsToPush
from .endpoints.push.remove_channels_from_push import RemoveChannelsFromPush
from .endpoints.push.remove_device import RemoveDeviceFromPush
from .endpoints.push.list_push_provisions import ListPushProvisions
from .managers import TelemetryManager

logger = logging.getLogger("pubnub")


class PubNubCore:
    """A base class for PubNub Python API implementations"""
    SDK_VERSION = "7.0.0"
    SDK_NAME = "PubNub-Python"

    TIMESTAMP_DIVIDER = 1000
    MAX_SEQUENCE = 65535

    __metaclass__ = ABCMeta
    _plugins = []

    def __init__(self, config):
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

    def add_channel_to_channel_group(self):
        return AddChannelToChannelGroup(self)

    def remove_channel_from_channel_group(self):
        return RemoveChannelFromChannelGroup(self)

    def list_channels_in_channel_group(self):
        return ListChannelsInChannelGroup(self)

    def remove_channel_group(self):
        return RemoveChannelGroup(self)

    def subscribe(self):
        return SubscribeBuilder(self._subscription_manager)

    def unsubscribe(self):
        return UnsubscribeBuilder(self._subscription_manager)

    def unsubscribe_all(self):
        return self._subscription_manager.unsubscribe_all()

    def reconnect(self):
        return self._subscription_manager.reconnect()

    def heartbeat(self):
        return Heartbeat(self)

    def set_state(self):
        return SetState(self, self._subscription_manager)

    def get_state(self):
        return GetState(self)

    def here_now(self):
        return HereNow(self)

    def where_now(self):
        return WhereNow(self)

    def publish(self):
        return Publish(self)

    def grant(self):
        return Grant(self)

    def grant_token(self):
        return GrantToken(self)

    def revoke_token(self, token):
        return RevokeToken(self, token)

    def audit(self):
        return Audit(self)

    # Push Related methods
    def list_push_channels(self):
        return ListPushProvisions(self)

    def add_channels_to_push(self):
        return AddChannelsToPush(self)

    def remove_channels_from_push(self):
        return RemoveChannelsFromPush(self)

    def remove_device_from_push(self):
        return RemoveDeviceFromPush(self)

    def history(self):
        return History(self)

    def message_counts(self):
        return MessageCount(self)

    def fire(self):
        return Fire(self)

    def signal(self):
        return Signal(self)

    def set_uuid_metadata(self):
        return SetUuid(self)

    def get_uuid_metadata(self):
        return GetUuid(self)

    def remove_uuid_metadata(self):
        return RemoveUuid(self)

    def get_all_uuid_metadata(self):
        return GetAllUuid(self)

    def set_channel_metadata(self):
        return SetChannel(self)

    def get_channel_metadata(self):
        return GetChannel(self)

    def remove_channel_metadata(self):
        return RemoveChannel(self)

    def get_all_channel_metadata(self):
        return GetAllChannels(self)

    def set_channel_members(self):
        return SetChannelMembers(self)

    def get_channel_members(self):
        return GetChannelMembers(self)

    def remove_channel_members(self):
        return RemoveChannelMembers(self)

    def manage_channel_members(self):
        return ManageChannelMembers(self)

    def set_memberships(self):
        return SetMemberships(self)

    def get_memberships(self):
        return GetMemberships(self)

    def manage_memberships(self):
        return ManageMemberships(self)

    def fetch_messages(self):
        return FetchMessages(self)

    def add_message_action(self):
        return AddMessageAction(self)

    def get_message_actions(self):
        return GetMessageActions(self)

    def remove_message_action(self):
        return RemoveMessageAction(self)

    def time(self):
        return Time(self)

    def delete_messages(self):
        return HistoryDelete(self)

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
            from .endpoints.file_operations.send_file_asyncio import AsyncioSendFile
            return AsyncioSendFile(self)
        else:
            raise NotImplementedError

    def download_file(self):
        if not self.sdk_platform():
            return DownloadFileNative(self)
        elif "Asyncio" in self.sdk_platform():
            from .endpoints.file_operations.download_file_asyncio import DownloadFileAsyncio
            return DownloadFileAsyncio(self)
        else:
            raise NotImplementedError

    def list_files(self):
        return ListFiles(self)

    def get_file_url(self):
        return GetFileDownloadUrl(self)

    def delete_file(self):
        return DeleteFile(self)

    def _fetch_file_upload_s3_data(self):
        return FetchFileUploadS3Data(self)

    def publish_file_message(self):
        return PublishFileMessage(self)

    def decrypt(self, cipher_key, file):
        return self.config.file_crypto.decrypt(cipher_key, file)

    def encrypt(self, cipher_key, file):
        return self.config.file_crypto.encrypt(cipher_key, file)

    @staticmethod
    def timestamp():
        return int(time.time())

    def _validate_subscribe_manager_enabled(self):
        if self._subscription_manager is None:
            raise Exception("Subscription manager is not enabled for this instance")

    """ Entities code -- all of methods bellow should be decorated with pubnub.features.feature_flag """
    @feature_flag('PN_ENABLE_ENTITIES')
    def add_memberships(self, user_id: str = None, users: list = None, space_id: str = None, spaces: list = None,
                        sync: bool = None):
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
    def update_memberships(self, user_id: str = None, users: list = None, space_id: str = None, spaces: list = None,
                           sync: bool = None):
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
        if len(kwargs) == 0:
            return RemoveMemberships(self)

        if 'user_id' in kwargs.keys() and 'space_id' in kwargs.keys():
            raise (PubNubException(pn_error=PNERR_MISUSE_OF_USER_AND_SPACE))

        if kwargs['user_id'] and kwargs['spaces']:
            membership = RemoveUserSpaces(self).user_id(kwargs['user_id']).spaces(kwargs['spaces'])
        elif kwargs['space_id'] and kwargs['users']:
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

    @feature_flag('PN_ENABLE_ENTITIES')
    def create_user(self, user_id: str, name: str = None, email: str = None, external_id: str = None,
                    profile_url: str = None, user_type: str = None, user_status: str = None, custom: dict = None,
                    sync: bool = None):
        user = CreateUser(self, user_id, name, email, external_id, profile_url, user_type, user_status, custom)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def update_user(self, user_id: str, name: str = None, email: str = None, external_id: str = None,
                    profile_url: str = None, user_type: str = None, user_status: str = None, custom: dict = None,
                    sync: bool = None):
        user = UpdateUser(self, user_id, name, email, external_id, profile_url, user_type, user_status, custom)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def upsert_user(self, user_id: str, name: str = None, email: str = None, external_id: str = None,
                    profile_url: str = None, user_type: str = None, user_status: str = None, custom: dict = None,
                    sync: bool = None):
        user = UpsertUser(self, user_id, name, email, external_id, profile_url, user_type, user_status, custom)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def remove_user(self, user_id: str, sync: bool = None):
        user = RemoveUser(self, user_id)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def fetch_user(self, user_id: str, include: list = [], sync: bool = None):
        user = FetchUser(self, user_id, include)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def fetch_users(self, limit: str = None, filter_string: str = None, include_total_count: bool = None,
                    include_custom: bool = None, page=None, sort_keys=None, sync: bool = None):
        user = FetchUsers(self, limit, filter_string, include_total_count, include_custom, page, sort_keys)

        if sync:
            return user.sync()
        return user

    @feature_flag('PN_ENABLE_ENTITIES')
    def create_space(self, space_id: str, name: str = None, description: str = None, space_type: str = None,
                     space_status: str = None, custom: dict = None, sync: bool = None):
        space = CreateSpace(self, space_id, name, description, space_type, space_status, custom)

        if sync:
            return space.sync()
        return space

    @feature_flag('PN_ENABLE_ENTITIES')
    def update_space(self, space_id: str, name: str = None, description: str = None, space_type: str = None,
                     space_status: str = None, custom: dict = None, sync: bool = None):
        space = UpdateSpace(self, space_id, name, description, space_type, space_status, custom)

        if sync:
            return space.sync()
        return space

    @feature_flag('PN_ENABLE_ENTITIES')
    def upsert_space(self, space_id: str, name: str = None, description: str = None, space_type: str = None,
                     space_status: str = None, custom: dict = None, sync: bool = None):
        space = UpsertSpace(self, space_id, name, description, space_type, space_status, custom)

        if sync:
            return space.sync()
        return space

    @feature_flag('PN_ENABLE_ENTITIES')
    def remove_space(self, space_id: str, sync: bool = None):
        space = RemoveSpace(self, space_id)

        if sync:
            return space.sync()
        return space

    @feature_flag('PN_ENABLE_ENTITIES')
    def fetch_space(self, space_id: str, include: list = [], sync: bool = None):
        space = FetchSpace(self, space_id, include)

        if sync:
            return space.sync()
        return space

    @feature_flag('PN_ENABLE_ENTITIES')
    def fetch_spaces(self, limit: str = None, filter_string: str = None, include_total_count: bool = None,
                     include_custom: bool = None, page=None, sort_keys=None, sync: bool = None):
        spaces = FetchSpaces(self, limit, filter_string, include_total_count, include_custom, page, sort_keys)

        if sync:
            return spaces.sync()
        return spaces
