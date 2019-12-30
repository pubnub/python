import unittest

from pubnub.crypto import PubNubCryptodome
from pubnub.models.consumer.access_manager import PNAccessManagerAuditResult, PNAccessManagerGrantResult
from pubnub.models.consumer.channel_group import PNChannelGroupsListResult, PNChannelGroupsAddChannelResult, \
    PNChannelGroupsRemoveGroupResult, PNChannelGroupsRemoveChannelResult
from pubnub.models.consumer.history import PNHistoryResult, PNHistoryItemResult
from pubnub.models.consumer.presence import PNHereNowResult, PNHereNowChannelData, PNHereNowOccupantsData, \
    PNWhereNowResult, PNSetStateResult, PNGetStateResult

from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.models.consumer.push import PNPushListProvisionsResult, PNPushAddChannelResult, PNPushRemoveChannelResult, \
    PNPushRemoveAllChannelsResult


class TestStringify(unittest.TestCase):
    def test_publish(self):
        assert str(PNPublishResult(None, 123123)) == "Publish success with timetoken 123123"

    def test_add_channel_to_group(self):
        assert str(PNChannelGroupsAddChannelResult()) == "Channel successfully added"

    def test_remove_channel_from_group(self):
        assert str(PNChannelGroupsRemoveChannelResult()) == "Channel successfully removed"

    def test_remove_channel_group(self):
        assert str(PNChannelGroupsRemoveGroupResult()) == "Group successfully removed"

    def test_list_channel_group(self):
        result = PNChannelGroupsListResult([
            'qwer',
            'asdf',
            'zxcv'
        ])

        assert str(result) == "Group contains following channels: qwer, asdf, zxcv"

    def test_audit(self):
        result = PNAccessManagerAuditResult(None, None, None, None, 3600, True, False, True, False)

        assert str(result) == \
            "Current permissions are valid for 3600 minutes: read True, write False, manage: True, delete: False"

    def test_grant(self):
        result = PNAccessManagerGrantResult(None, None, None, None, 3600, True, False, True, False)

        assert str(result) == \
            "New permissions are set for 3600 minutes: read True, write False, manage: True, delete: False"

    def test_history(self):
        assert str(PNHistoryResult(None, 123, 789)) == "History result for range 123..789"

    def test_history_item(self):
        assert str(PNHistoryItemResult({'blah': 2}, PubNubCryptodome(), 123)) == \
            "History item with tt: 123 and content: {'blah': 2}"

        assert str(PNHistoryItemResult({'blah': 2}, PubNubCryptodome())) == \
            "History item with tt: None and content: {'blah': 2}"

    def test_here_now(self):
        assert str(PNHereNowResult(7, 4, None)) == "HereNow Result total occupancy: 4, total channels: 7"

    def test_here_now_channel_data(self):
        assert str(PNHereNowChannelData('blah', 5, 9)) == \
            "HereNow Channel Data for channel 'blah': occupancy: 5, occupants: 9"

    def test_here_now_occupants_data(self):
        assert str(PNHereNowOccupantsData('myuuid', {'blah': 3})) == \
            "HereNow Occupants Data for 'myuuid': {'blah': 3}"

    def test_where_now(self):
        assert str(PNWhereNowResult(['qwer', 'asdf'])) == \
            "User is currently subscribed to qwer, asdf"

    def test_set_state(self):
        assert str(PNSetStateResult({})) == "New state {} successfully set"

    def test_get_state(self):
        assert str(PNGetStateResult({})) == "Current state is {}"

    def test_push_list(self):
        assert str(PNPushListProvisionsResult(['qwer', 'asdf'])) == \
            "Push notification enabled on following channels: qwer, asdf"

    def test_push_add(self):
        assert str(PNPushAddChannelResult()) == \
            "Channel successfully added"

    def test_push_remove(self):
        assert str(PNPushRemoveChannelResult()) == \
            "Channel successfully removed"

    def test_push_remove_all(self):
        assert str(PNPushRemoveAllChannelsResult()) == \
            "All channels successfully removed"
