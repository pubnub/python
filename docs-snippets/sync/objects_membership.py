"""Docs page: App Context (sync). Channel memberships, channel members and the PNChannelMembership and PNUUID classes.

User and channel metadata are in objects.py. The helpers below repeat the ones in that module because a page module
cannot import a sibling file. Every object a step creates is removed in a finally block.
"""
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.objects_v2.channel_members import PNUUID
from pubnub.models.consumer.objects_v2.common import MemberIncludes, MembershipIncludes
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
from pubnub.models.consumer.objects_v2.page import Next, Previous
from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue

from harness import assertions as a
from harness import names
from harness import world
from harness.step import step
from harness.wait import eventually

REGISTERED_NAMES = [
    'some_uuid', 'some_uuid_with_custom', 'some_uuid_named', 'somechannel', 'somechannel_with_custom',
    'channel_id', 'channel_id_named',
]

CUSTOM_1 = {'key3': 'val1', 'key4': 'val2'}
CUSTOM_2 = {'key5': 'val1', 'key6': 'val2'}


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
        world.record('uuid_metadata', uid)
    for channel in channels:
        world.record('channel_metadata', channel)


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


def gone(read):
    """The read raises a 404 once the object is removed."""
    eventually(lambda: a.raises(PubNubException, read, match='404'), what='object reports 404')


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


@step('get_memberships_builder', 'get_memberships_named', role='open')
def test_get_memberships(clients):
    pubnub = clients.sync('open', 'reader')
    uid = names.with_suffix('some_uuid')
    plain = names.with_suffix('somechannel')
    with_custom = names.with_suffix('somechannel_with_custom')
    record([uid], [plain, with_custom])
    try:
        seed_channels(pubnub, plain, with_custom)
        seed_memberships(pubnub, uid, plain, with_custom)

        # snippet.get_memberships_builder
        # snippet.hide
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        # snippet.show
        envelope = pubnub.get_memberships() \
            .include(MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .uuid("some_uuid").sync()
        # snippet.end

        check_memberships(envelope.result.data, plain, with_custom)
        a.eq(envelope.result.status, 200)

        # snippet.get_memberships_named
        envelope = pubnub.get_memberships(uuid="some_uuid",
                                          include=MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .sync()
        # snippet.end

        check_memberships(envelope.result.data, plain, with_custom)

        # Details appear only when they are included
        bare = pubnub.get_memberships(uuid=uid).sync().result.data
        a.not_contains(bare[0], 'custom', 'custom only when included')
        a.eq(bare[0]['channel'], {'id': bare[0]['channel']['id']}, 'channel is only an id by default')
        only_custom = pubnub.get_memberships(uuid=uid, include=MembershipIncludes(custom=True)).sync().result.data
        a.contains(only_custom[0], 'custom')
        a.eq(by_channel(only_custom)[with_custom]['custom'], CUSTOM_2)
        a.not_contains(bare[0], 'type')
        a.not_contains(bare[0], 'status')
        typed = PNChannelMembership(plain, status='active', type='doc')
        pubnub.set_memberships(uuid=uid, channel_memberships=[typed]).sync()
        shown = pubnub.get_memberships(uuid=uid, include=MembershipIncludes(type=True, status=True)).sync()
        a.eq((by_channel(shown.result.data)[plain]['type'], by_channel(shown.result.data)[plain]['status']),
             ('doc', 'active'))

        filtered = pubnub.get_memberships(uuid=uid, filter="channel.name LIKE 'some name with*'").sync().result.data
        a.eq(channel_ids(filtered), [with_custom], 'filter on the channel name')
        counted = pubnub.get_memberships(uuid=uid).include_total_count(True).sync().result
        a.eq(counted.total_count, 2, 'total count')

        # Paging with next and prev, sorted by the update time (the only sort key the service accepts here)
        newest = [PNSortKey.desc(PNSortKeyValue.UPDATED)]
        first = pubnub.get_memberships(uuid=uid, limit=1, sort_keys=newest).sync().result
        a.eq(len(first.data), 1)
        a.ok(isinstance(first.next, Next), 'next page token')
        second = pubnub.get_memberships(uuid=uid, limit=1, sort_keys=newest, page=first.next).sync().result
        a.eq(sorted(channel_ids(first.data + second.data)), sorted([plain, with_custom]), 'two pages cover both')
        a.ok(isinstance(second.prev, Previous), 'prev page token')
        back = pubnub.get_memberships(uuid=uid, limit=1, sort_keys=newest, page=second.prev).sync().result
        a.eq(channel_ids(back.data), channel_ids(first.data), 'prev returns the first page')
    finally:
        cleanup(pubnub, [uid], [plain, with_custom])


@step('set_memberships_builder', 'set_memberships_named', role='open', timeout=180)
def test_set_memberships(clients):
    pubnub = clients.sync('open', 'setter')
    first = names.with_suffix('some_uuid')
    second = names.with_suffix('some_uuid_named')
    plain = names.with_suffix('somechannel')
    with_custom = names.with_suffix('somechannel_with_custom')
    record([first, second], [plain, with_custom])
    try:
        seen = watch(clients, first)

        # snippet.set_memberships_builder
        # snippet.hide
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
        # snippet.show
        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        pubnub.set_channel_metadata() \
            .channel(some_channel) \
            .set_name("some name") \
            .sync()

        custom_1 = {
            "key3": "val1",
            "key4": "val2",
        }

        pubnub.set_channel_metadata() \
            .channel(some_channel_with_custom) \
            .set_name("some name with custom") \
            .custom(custom_1) \
            .sync()

        custom_2 = {
            "key5": "val1",
            "key6": "val2",
        }

        channel_memberships_to_set = [
            PNChannelMembership.channel(some_channel),
            PNChannelMembership.channel_with_custom(some_channel_with_custom, custom_2),
        ]

        envelope = pubnub.set_memberships() \
            .uuid("some_uuid") \
            .channel_memberships(channel_memberships_to_set) \
            .include(MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .sync()
        # snippet.end

        check_memberships(envelope.result.data, plain, with_custom)
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['uuid']['id']), ('membership', 'set', first))
        a.contains([plain, with_custom], payload['channel']['id'])

        seen = watch(clients, second)

        # snippet.set_memberships_named
        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        pubnub.set_channel_metadata(channel=some_channel, name="some name").sync()

        custom_1 = {
            "key3": "val1",
            "key4": "val2",
        }

        pubnub.set_channel_metadata(channel=some_channel_with_custom,
                                    name="some name with custom",
                                    custom=custom_1) \
            .sync()

        custom_2 = {
            "key5": "val1",
            "key6": "val2",
        }

        channel_memberships_to_set = [
            PNChannelMembership.channel(some_channel),
            PNChannelMembership.channel_with_custom(some_channel_with_custom, custom_2),
        ]

        envelope = pubnub.set_memberships(uuid="some_uuid_named",
                                          channel_memberships=channel_memberships_to_set,
                                          include=MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .sync()
        # snippet.end

        check_memberships(envelope.result.data, plain, with_custom)
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['uuid']['id']), ('membership', 'set', second))

        # The channel side sees the same memberships
        members = pubnub.get_channel_members(channel=plain).sync().result.data
        a.eq(sorted(member_ids(members)), sorted([first, second]), 'both users are members')

        # Set adds to the stored memberships, it does not replace them
        extra = names.with_suffix('somechannel_extra')
        record(channels=[extra])
        try:
            pubnub.set_channel_metadata(channel=extra, name='extra').sync()
            added = pubnub.set_memberships(uuid=first, channel_memberships=[PNChannelMembership.channel(extra)]).sync()
            a.eq(sorted(channel_ids(added.result.data)), sorted([plain, with_custom, extra]), 'set keeps the others')
        finally:
            cleanup(pubnub, [first], [extra])
    finally:
        cleanup(pubnub, [first, second], [plain, with_custom])


@step('remove_memberships_builder', 'remove_memberships_named', role='open', timeout=180)
def test_remove_memberships(clients):
    pubnub = clients.sync('open', 'remover')
    first = names.with_suffix('some_uuid')
    second = names.with_suffix('some_uuid_named')
    plain = names.with_suffix('somechannel')
    with_custom = names.with_suffix('somechannel_with_custom')
    record([first, second], [plain, with_custom])
    try:
        seed_channels(pubnub, plain, with_custom)
        for uid in (first, second):
            seed_memberships(pubnub, uid, plain, with_custom)
        seen = watch(clients, first)

        # snippet.remove_memberships_builder
        # snippet.hide
        from pubnub.endpoints.objects_v2.objects_endpoint import ChannelIncludeEndpoint
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
        # snippet.show
        some_channel = "somechannel"

        envelope = pubnub.remove_memberships() \
            .uuid("some_uuid") \
            .channel_memberships([PNChannelMembership.channel(some_channel)]) \
            .include_custom(True) \
            .include_channel(ChannelIncludeEndpoint.CHANNEL_WITH_CUSTOM) \
            .sync()
        # snippet.end

        left = envelope.result.data
        a.eq(channel_ids(left), [with_custom], 'the response lists the remaining memberships')
        a.eq(left[0]['custom'], CUSTOM_2)
        a.eq(left[0]['channel']['custom'], CUSTOM_1)
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['uuid']['id'], payload['channel']['id']), ('membership', 'delete', first, plain))
        eventually(lambda: a.eq(channel_ids(pubnub.get_memberships(uuid=first).sync().result.data), [with_custom]),
                   what='membership removed')
        a.eq(len(pubnub.get_memberships(uuid=second).sync().result.data), 2, 'other users keep theirs')

        # snippet.remove_memberships_named
        envelope = pubnub.remove_memberships(uuid="some_uuid_named",
                                             channel_memberships=[PNChannelMembership.channel(some_channel)],
                                             include=MembershipIncludes(custom=True, channel=True,
                                                                        channel_custom=True)) \
            .sync()
        # snippet.end

        a.eq(channel_ids(envelope.result.data), [with_custom])
        a.eq(envelope.result.data[0]['channel']['custom'], CUSTOM_1)
        eventually(lambda: a.eq(channel_ids(pubnub.get_memberships(uuid=second).sync().result.data), [with_custom]),
                   what='second membership removed')
        a.eq(pubnub.get_channel_metadata(channel=plain).sync().result.data['id'], plain, 'the channel stays')
    finally:
        cleanup(pubnub, [first, second], [plain, with_custom])


@step('manage_memberships_builder', 'manage_memberships_named', role='open', timeout=180)
def test_manage_memberships(clients):
    pubnub = clients.sync('open', 'manager')
    first = names.with_suffix('some_uuid')
    second = names.with_suffix('some_uuid_named')
    plain = names.with_suffix('somechannel')
    with_custom = names.with_suffix('somechannel_with_custom')
    record([first, second], [plain, with_custom])
    try:
        seed_channels(pubnub, plain, with_custom)
        for uid in (first, second):
            seed_one_membership(pubnub, uid, with_custom)
        eventually(lambda: a.eq(channel_ids(pubnub.get_memberships(uuid=second).sync().result.data), [with_custom]),
                   what='seed visible')
        seen = watch(clients, first)

        # snippet.manage_memberships_builder
        # snippet.hide
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
        # snippet.show
        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        envelope = pubnub.manage_memberships() \
            .uuid("some_uuid") \
            .set([PNChannelMembership.channel(some_channel)]) \
            .remove([PNChannelMembership.channel(some_channel_with_custom)]) \
            .include(MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .sync()
        # snippet.end

        a.eq(channel_ids(envelope.result.data), [plain], 'the response lists the remaining memberships')
        a.eq(envelope.result.data[0]['channel']['name'], 'some name')
        kind, event, payload = first_event(seen)
        a.eq(kind, 'membership')
        a.contains([('set', plain), ('delete', with_custom)], (event, payload['channel']['id']))
        eventually(lambda: a.eq(channel_ids(pubnub.get_memberships(uuid=first).sync().result.data), [plain]),
                   what='memberships changed')

        # snippet.manage_memberships_named
        envelope = pubnub.manage_memberships(uuid="some_uuid_named",
                                             channel_memberships_to_set=[PNChannelMembership.channel(some_channel)],
                                             channel_memberships_to_remove=[
                                                 PNChannelMembership.channel(some_channel_with_custom)],
                                             include=MembershipIncludes(custom=True, channel=True,
                                                                        channel_custom=True)) \
            .sync()
        # snippet.end

        a.eq(channel_ids(envelope.result.data), [plain])
        eventually(lambda: a.eq(channel_ids(pubnub.get_memberships(uuid=second).sync().result.data), [plain]),
                   what='second user changed')
    finally:
        cleanup(pubnub, [first, second], [plain, with_custom])


@step('get_channel_members_builder', 'get_channel_members_named', role='open')
def test_get_channel_members(clients):
    pubnub = clients.sync('open', 'reader')
    channel = names.with_suffix('channel_id')
    plain = names.with_suffix('some_uuid')
    with_custom = names.with_suffix('some_uuid_with_custom')
    record([plain, with_custom], [channel])
    try:
        seed_users(pubnub, plain, with_custom)
        pubnub.set_channel_metadata(channel=channel, name='Doc channel').sync()
        seed_members(pubnub, channel, plain, with_custom)

        # snippet.get_channel_members_builder
        # snippet.hide
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        # snippet.show
        envelope = pubnub.get_channel_members() \
            .channel("channel_id") \
            .include(MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        check_members(envelope.result.data, plain, with_custom)
        a.eq(envelope.result.status, 200)

        # snippet.get_channel_members_named
        envelope = pubnub.get_channel_members(channel="channel_id",
                                              include=MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        check_members(envelope.result.data, plain, with_custom)

        bare = pubnub.get_channel_members(channel=channel).sync().result.data
        a.not_contains(bare[0], 'custom', 'custom only when included')
        a.eq(bare[0]['uuid'], {'id': bare[0]['uuid']['id']}, 'the user is only an id by default')
        only_custom = pubnub.get_channel_members(channel=channel, include=MemberIncludes(custom=True)).sync()
        a.eq(by_member(only_custom.result.data)[with_custom]['custom'], CUSTOM_2)

        # Member filters address the user as uuid.name, uuid.description is not a filter property
        filtered = pubnub.get_channel_members(channel=channel, filter="uuid.name LIKE 'some name with*'").sync()
        a.eq(member_ids(filtered.result.data), [with_custom], 'filter on the user name')
        counted = pubnub.get_channel_members(channel=channel).include_total_count(True).sync().result
        a.eq(counted.total_count, 2, 'total count')

        newest = [PNSortKey.desc(PNSortKeyValue.UPDATED)]
        first = pubnub.get_channel_members(channel=channel, limit=1, sort_keys=newest).sync().result
        a.eq(len(first.data), 1)
        a.ok(isinstance(first.next, Next), 'next page token')
        second = pubnub.get_channel_members(channel=channel, limit=1, sort_keys=newest, page=first.next).sync().result
        a.eq(sorted(member_ids(first.data + second.data)), sorted([plain, with_custom]), 'two pages cover both')
        a.ok(isinstance(second.prev, Previous), 'prev page token')
        back = pubnub.get_channel_members(channel=channel, limit=1, sort_keys=newest, page=second.prev).sync().result
        a.eq(member_ids(back.data), member_ids(first.data), 'prev returns the first page')
    finally:
        cleanup(pubnub, [plain, with_custom], [channel])


@step('set_channel_members_builder', 'set_channel_members_named', role='open', timeout=180)
def test_set_channel_members(clients):
    pubnub = clients.sync('open', 'setter')
    first = names.with_suffix('channel_id')
    second = names.with_suffix('channel_id_named')
    plain = names.with_suffix('some_uuid')
    with_custom = names.with_suffix('some_uuid_with_custom')
    record([plain, with_custom], [first, second])
    try:
        seen = watch(clients, first)

        # snippet.set_channel_members_builder
        # snippet.hide
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        # snippet.show
        pubnub.set_uuid_metadata() \
            .uuid("some_uuid") \
            .set_name("some name") \
            .sync()

        custom_1 = {
            "key3": "val1",
            "key4": "val2"
        }

        pubnub.set_uuid_metadata() \
            .uuid("some_uuid_with_custom") \
            .set_name("some name with custom") \
            .custom(custom_1) \
            .sync()

        custom_2 = {
            "key5": "val1",
            "key6": "val2"
        }

        uuids_to_set = [
            PNUUID.uuid("some_uuid"),
            PNUUID.uuid_with_custom("some_uuid_with_custom", custom_2)
        ]

        envelope = pubnub.set_channel_members() \
            .channel("channel_id") \
            .uuids(uuids_to_set) \
            .include(MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        check_members(envelope.result.data, plain, with_custom)
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['channel']['id']), ('membership', 'set', first))
        a.contains([plain, with_custom], payload['uuid']['id'])

        seen = watch(clients, second)

        # snippet.set_channel_members_named
        pubnub.set_uuid_metadata(uuid="some_uuid", name="some name").sync()

        custom_1 = {
            "key3": "val1",
            "key4": "val2"
        }

        pubnub.set_uuid_metadata(uuid="some_uuid_with_custom",
                                 name="some name with custom",
                                 custom=custom_1) \
            .sync()

        custom_2 = {
            "key5": "val1",
            "key6": "val2"
        }

        uuids_to_set = [
            PNUUID.uuid("some_uuid"),
            PNUUID.uuid_with_custom("some_uuid_with_custom", custom_2)
        ]

        envelope = pubnub.set_channel_members(channel="channel_id_named",
                                              uuids=uuids_to_set,
                                              include=MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        check_members(envelope.result.data, plain, with_custom)
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['channel']['id']), ('membership', 'set', second))

        memberships = pubnub.get_memberships(uuid=plain).sync().result.data
        a.eq(sorted(channel_ids(memberships)), sorted([first, second]), 'the user side sees both channels')

        # Set adds to the stored members, it does not replace them
        extra = names.with_suffix('some_uuid_extra')
        record(uuids=[extra])
        try:
            pubnub.set_uuid_metadata(uuid=extra, name='extra').sync()
            added = pubnub.set_channel_members(channel=first, uuids=[PNUUID.uuid(extra)]).sync()
            a.eq(sorted(member_ids(added.result.data)), sorted([plain, with_custom, extra]), 'set keeps the others')
        finally:
            cleanup(pubnub, [extra], [])
    finally:
        cleanup(pubnub, [plain, with_custom], [first, second])


@step('remove_channel_members_builder', 'remove_channel_members_named', role='open', timeout=180)
def test_remove_channel_members(clients):
    pubnub = clients.sync('open', 'remover')
    first = names.with_suffix('channel_id')
    second = names.with_suffix('channel_id_named')
    plain = names.with_suffix('some_uuid')
    with_custom = names.with_suffix('some_uuid_with_custom')
    record([plain, with_custom], [first, second])
    try:
        seed_users(pubnub, plain, with_custom)
        for channel in (first, second):
            pubnub.set_channel_metadata(channel=channel, name='Doc channel').sync()
            seed_members(pubnub, channel, plain, with_custom)
        seen = watch(clients, first)

        # snippet.remove_channel_members_builder
        # snippet.hide
        from pubnub.endpoints.objects_v2.objects_endpoint import UUIDIncludeEndpoint
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID
        # snippet.show
        envelope = pubnub.remove_channel_members() \
            .channel("channel_id") \
            .uuids([PNUUID.uuid("some_uuid")]) \
            .include_custom(True) \
            .include_uuid(UUIDIncludeEndpoint.UUID_WITH_CUSTOM) \
            .sync()
        # snippet.end

        left = envelope.result.data
        a.eq(member_ids(left), [with_custom], 'the response lists the remaining members')
        a.eq(left[0]['custom'], CUSTOM_2)
        a.eq(left[0]['uuid']['custom'], CUSTOM_1)
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['channel']['id'], payload['uuid']['id']), ('membership', 'delete', first, plain))
        eventually(lambda: a.eq(member_ids(pubnub.get_channel_members(channel=first).sync().result.data),
                                [with_custom]), what='member removed')
        a.eq(len(pubnub.get_channel_members(channel=second).sync().result.data), 2, 'other channels keep theirs')

        # snippet.remove_channel_members_named
        envelope = pubnub.remove_channel_members(channel="channel_id_named",
                                                 uuids=[PNUUID.uuid("some_uuid")],
                                                 include=MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        a.eq(member_ids(envelope.result.data), [with_custom])
        a.eq(envelope.result.data[0]['uuid']['custom'], CUSTOM_1)
        eventually(lambda: a.eq(member_ids(pubnub.get_channel_members(channel=second).sync().result.data),
                                [with_custom]), what='second member removed')
        a.eq(pubnub.get_uuid_metadata(uuid=plain).sync().result.data['id'], plain, 'the user stays')
    finally:
        cleanup(pubnub, [plain, with_custom], [first, second])


@step('manage_channel_members_builder', 'manage_channel_members_named', role='open', timeout=180)
def test_manage_channel_members(clients):
    pubnub = clients.sync('open', 'manager')
    first = names.with_suffix('channel_id')
    second = names.with_suffix('channel_id_named')
    plain = names.with_suffix('some_uuid')
    with_custom = names.with_suffix('some_uuid_with_custom')
    record([plain, with_custom], [first, second])
    try:
        seed_users(pubnub, plain, with_custom)
        for channel in (first, second):
            pubnub.set_channel_metadata(channel=channel, name='Doc channel').sync()
            seed_one_member(pubnub, channel, with_custom)
        eventually(lambda: a.eq(member_ids(pubnub.get_channel_members(channel=second).sync().result.data),
                                [with_custom]), what='seed visible')
        seen = watch(clients, first)

        # snippet.manage_channel_members_builder
        # snippet.hide
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        # snippet.show
        envelope = pubnub.manage_channel_members() \
            .channel("channel_id") \
            .set([PNUUID.uuid("some_uuid")]) \
            .remove([PNUUID.uuid("some_uuid_with_custom")]) \
            .include(MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        a.eq(member_ids(envelope.result.data), [plain], 'the response lists the remaining members')
        a.eq(envelope.result.data[0]['uuid']['name'], 'some name')
        kind, event, payload = first_event(seen)
        a.eq(kind, 'membership')
        a.contains([('set', plain), ('delete', with_custom)], (event, payload['uuid']['id']))
        eventually(lambda: a.eq(member_ids(pubnub.get_channel_members(channel=first).sync().result.data), [plain]),
                   what='members changed')

        # snippet.manage_channel_members_named
        envelope = pubnub.manage_channel_members(channel="channel_id_named",
                                                 uuids_to_set=[PNUUID.uuid("some_uuid")],
                                                 uuids_to_remove=[PNUUID.uuid("some_uuid_with_custom")],
                                                 include=MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        a.eq(member_ids(envelope.result.data), [plain])
        eventually(lambda: a.eq(member_ids(pubnub.get_channel_members(channel=second).sync().result.data), [plain]),
                   what='second channel changed')
    finally:
        cleanup(pubnub, [plain, with_custom], [first, second])


@step('pnchannelmembership_class', role='open')
def test_channel_membership_class(clients):
    pubnub = clients.sync('open', 'classes')
    uid = names.with_suffix('some_uuid')
    plain = names.with_suffix('somechannel')
    with_custom = names.with_suffix('somechannel_with_custom')
    record([uid], [plain, with_custom])
    try:
        seed_channels(pubnub, plain, with_custom)

        # snippet.pnchannelmembership_class
        # snippet.hide
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
        # snippet.show
        membership = PNChannelMembership.channel("somechannel")
        membership_with_custom = PNChannelMembership.channel_with_custom("somechannel_with_custom",
                                                                         {"key5": "val1", "key6": "val2"})
        # snippet.end

        a.eq(type(membership).__name__, 'JustChannel')
        a.eq(type(membership_with_custom).__name__, 'ChannelWithCustom')
        a.eq(membership.to_payload_dict(), {'channel': {'id': plain}})
        a.eq(membership_with_custom.to_payload_dict(), {'channel': {'id': with_custom}, 'custom': CUSTOM_2})
        pubnub.set_memberships(uuid=uid, channel_memberships=[membership, membership_with_custom]).sync()
        eventually(lambda: a.eq(sorted(channel_ids(pubnub.get_memberships(uuid=uid).sync().result.data)),
                                sorted([plain, with_custom])), what='memberships set from the helper objects')
        found = pubnub.get_memberships(uuid=uid, include=MembershipIncludes(custom=True)).sync().result.data
        a.eq(by_channel(found)[with_custom]['custom'], CUSTOM_2)
        a.eq(by_channel(found)[plain]['custom'], None)
    finally:
        cleanup(pubnub, [uid], [plain, with_custom])


@step('pnuuid_class', role='open')
def test_uuid_class(clients):
    pubnub = clients.sync('open', 'classes')
    channel = names.with_suffix('channel_id')
    plain = names.with_suffix('some_uuid')
    with_custom = names.with_suffix('some_uuid_with_custom')
    record([plain, with_custom], [channel])
    try:
        seed_users(pubnub, plain, with_custom)
        pubnub.set_channel_metadata(channel=channel, name='Doc channel').sync()

        # snippet.pnuuid_class
        # snippet.hide
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID
        # snippet.show
        member = PNUUID.uuid("some_uuid")
        member_with_custom = PNUUID.uuid_with_custom("some_uuid_with_custom", {"key5": "val1", "key6": "val2"})
        # snippet.end

        a.eq(type(member).__name__, 'JustUUID')
        a.eq(type(member_with_custom).__name__, 'UUIDWithCustom')
        a.eq(member.to_payload_dict(), {'uuid': {'id': plain}})
        a.eq(member_with_custom.to_payload_dict(), {'uuid': {'id': with_custom}, 'custom': CUSTOM_2})
        pubnub.set_channel_members(channel=channel, uuids=[member, member_with_custom]).sync()
        eventually(lambda: a.eq(sorted(member_ids(pubnub.get_channel_members(channel=channel).sync().result.data)),
                                sorted([plain, with_custom])), what='members set from the helper objects')
        found = pubnub.get_channel_members(channel=channel, include=MemberIncludes(custom=True)).sync().result.data
        a.eq(by_member(found)[with_custom]['custom'], CUSTOM_2)
        a.eq(by_member(found)[plain]['custom'], None)
    finally:
        cleanup(pubnub, [plain, with_custom], [channel])
