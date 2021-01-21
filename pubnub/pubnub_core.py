import logging
import time

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
from .managers import BasePathManager, TokenManager, TokenManagerProperties
from .builders import SubscribeBuilder
from .builders import UnsubscribeBuilder
from .endpoints.time import Time
from .endpoints.history import History
from .endpoints.access.audit import Audit
from .endpoints.access.grant import Grant
from .endpoints.access.grant_token import GrantToken
from .endpoints.access.revoke import Revoke
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
    SDK_VERSION = "5.0.0"
    SDK_NAME = "PubNub-Python"

    TIMESTAMP_DIVIDER = 1000
    MAX_SEQUENCE = 65535

    __metaclass__ = ABCMeta

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

    def revoke(self):
        return Revoke(self)

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

    def remove_memberships(self):
        return RemoveMemberships(self)

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

    def set_token(self, token):
        self._token_manager.set_token(token)

    def set_tokens(self, tokens):
        self._token_manager.set_tokens(tokens)

    def get_token(self, tms_properties):
        return self._token_manager.get_token(tms_properties)

    def get_token_by_resource(self, resource_id, resource_type):
        return self._token_manager.get_token(TokenManagerProperties(
            resource_id=resource_id,
            resource_type=resource_type
        ))

    def get_tokens(self):
        return self._token_manager.get_tokens()

    def get_tokens_by_resource(self, resource_type):
        return self._token_manager.get_tokens_by_resource(resource_type)

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
