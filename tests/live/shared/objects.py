"""Shared scenario data of the objects page for both docsets: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the sync and asyncio tests call outside
the snippet markers. Moved from the old docs-snippets/<docset>/ modules. Coroutine twins of a sync helper
carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
from pubnub.models.consumer.objects_v2.channel_members import PNUUID

from support import assertions as a
from support import cleanup as live_cleanup
from support.wait import eventually

NAMES = [
    'channel_id',
    'channel_id_named',
    'doc_channel_a',
    'doc_channel_b',
    'doc_channel_c',
    'doc_missing',
    'doc_missing_channel',
    'doc_other',
    'doc_type',
    'doc_user_a',
    'doc_user_b',
    'doc_user_c',
    'some_uuid',
    'some_uuid_extra',
    'some_uuid_named',
    'some_uuid_with_custom',
    'somechannel',
    'somechannel_extra',
    'somechannel_with_custom',
]


UUID_FIELDS = {
    'name': 'Some Name',
    'status': 'Active',
    'type': 'User',
    'email': 'test@example.com',
    'profileUrl': 'http://example.com',
    'externalId': '1234567890',
}


class AppContextEvents(SubscribeCallback):
    """Collects App Context events.

    The sync SDK stops its message worker with an AttributeError right after it hands the first App Context event
    to the listeners (models/subscription.py:314-324). A watcher therefore sees exactly one event, so a step
    creates one watcher per change it wants to observe.
    """
    def __init__(self):
        self.categories = []
        self.items = []

    def status(self, pubnub, status):
        self.categories.append(status.category)

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        pass

    def uuid(self, pubnub, uuid):
        self.items.append(('uuid', uuid.event, uuid.data))

    def channel(self, pubnub, channel):
        self.items.append(('channel', channel.event, channel.data))

    def membership(self, pubnub, membership):
        self.items.append(('membership', membership.event, membership.data))


def watch(clients, *channels):
    """A second client that listens on the given channels. Returns after it is connected."""
    client = clients.sync('open', 'watcher')
    seen = AppContextEvents()
    client.subscribed_by_suite = True
    client.add_listener(seen)
    client.subscribe().channels(list(channels)).execute()
    eventually(lambda: a.ok(PNStatusCategory.PNConnectedCategory in seen.categories, 'not connected yet'),
               timeout=15, what='watcher connected')
    return seen


def first_event(seen):
    eventually(lambda: a.ok(len(seen.items) >= 1, 'no App Context event yet'), timeout=20, what='App Context event')
    return seen.items[0]


def quiet_404(call):
    """Run a cleanup call. A missing object is fine, any other error is not."""
    try:
        return call()
    except PubNubException as e:
        if '404' not in str(e):
            raise
    return None


def cleanup(pubnub, uuids=(), channels=()):
    """Remove memberships first, then the metadata objects."""
    for uid in uuids:
        found = quiet_404(lambda: pubnub.get_memberships(uuid=uid, limit=100).sync())
        if found and found.result.data:
            leftovers = [PNChannelMembership.channel(m['channel']['id']) for m in found.result.data]
            quiet_404(lambda: pubnub.remove_memberships(uuid=uid, channel_memberships=leftovers).sync())
    for channel in channels:
        quiet_404(lambda: pubnub.remove_channel_metadata(channel=channel).sync())
    for uid in uuids:
        quiet_404(lambda: pubnub.remove_uuid_metadata(uuid=uid).sync())


def record(uuids=(), channels=()):
    for uid in uuids:
        live_cleanup.record('uuid_metadata', uid)
    for channel in channels:
        live_cleanup.record('channel_metadata', channel)


def ids(items):
    return [item['id'] for item in items]


def gone(read):
    """The read raises a 404 once the object is removed."""
    eventually(lambda: a.raises(PubNubException, read, match='404'), what='object reports 404')


CUSTOM_1 = {'key3': 'val1', 'key4': 'val2'}


CUSTOM_2 = {'key5': 'val1', 'key6': 'val2'}


def channel_ids(items):
    return [item['channel']['id'] for item in items]


def member_ids(items):
    return [item['uuid']['id'] for item in items]


def by_channel(items):
    return {item['channel']['id']: item for item in items}


def by_member(items):
    return {item['uuid']['id']: item for item in items}


def seed_channels(pubnub, plain, with_custom):
    pubnub.set_channel_metadata(channel=plain, name='some name').sync()
    pubnub.set_channel_metadata(channel=with_custom, name='some name with custom', custom=CUSTOM_1).sync()


def seed_users(pubnub, plain, with_custom):
    pubnub.set_uuid_metadata(uuid=plain, name='some name').sync()
    pubnub.set_uuid_metadata(uuid=with_custom, name='some name with custom', custom=CUSTOM_1).sync()


def seed_memberships(pubnub, uid, plain, with_custom):
    pubnub.set_memberships(uuid=uid, channel_memberships=[
        PNChannelMembership.channel(plain), PNChannelMembership.channel_with_custom(with_custom, CUSTOM_2)]).sync()


def seed_one_membership(pubnub, uid, with_custom):
    pubnub.set_memberships(uuid=uid, channel_memberships=[
        PNChannelMembership.channel_with_custom(with_custom, CUSTOM_2)]).sync()


def seed_one_member(pubnub, channel, with_custom):
    pubnub.set_channel_members(channel=channel, uuids=[PNUUID.uuid_with_custom(with_custom, CUSTOM_2)]).sync()


def seed_members(pubnub, channel, plain, with_custom):
    pubnub.set_channel_members(channel=channel, uuids=[
        PNUUID.uuid(plain), PNUUID.uuid_with_custom(with_custom, CUSTOM_2)]).sync()


def check_memberships(items, plain, with_custom):
    """Both memberships with the details MembershipIncludes(custom, channel, channel_custom) asks for."""
    a.eq(sorted(channel_ids(items)), sorted([plain, with_custom]))
    found = by_channel(items)
    a.eq(found[plain]['custom'], None, 'plain membership has no custom')
    a.eq(found[with_custom]['custom'], CUSTOM_2, 'membership custom')
    a.eq(found[plain]['channel']['name'], 'some name')
    a.eq(found[with_custom]['channel']['custom'], CUSTOM_1, 'channel custom')
    a.eq(found[with_custom]['channel']['name'], 'some name with custom')
    a.ok(found[plain]['eTag'] and found[plain]['updated'], 'eTag and updated are returned')


def check_members(items, plain, with_custom):
    a.eq(sorted(member_ids(items)), sorted([plain, with_custom]))
    found = by_member(items)
    a.eq(found[plain]['custom'], None, 'plain member has no custom')
    a.eq(found[with_custom]['custom'], CUSTOM_2, 'member custom')
    a.eq(found[plain]['uuid']['name'], 'some name')
    a.eq(found[with_custom]['uuid']['custom'], CUSTOM_1, 'user custom')
    a.eq(found[with_custom]['uuid']['name'], 'some name with custom')
