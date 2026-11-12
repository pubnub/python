"""Docs page: App Context (sync). User and channel metadata.

Memberships, members and the two helper classes are in objects_membership.py.
Every object a step creates is removed in a finally block. The janitor also removes leftovers that carry the run
marker and are older than six hours.
"""
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
from pubnub.models.consumer.objects_v2.page import Next, Previous

from harness import assertions as a
from harness import names
from harness import world
from harness.step import step
from harness.wait import eventually

REGISTERED_NAMES = [
    'some_uuid', 'some_uuid_named', 'channel_id', 'channel_id_named', 'doc_type',
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
        world.record('uuid_metadata', uid)
    for channel in channels:
        world.record('channel_metadata', channel)


def ids(items):
    return [item['id'] for item in items]


def gone(read):
    """The read raises a 404 once the object is removed."""
    eventually(lambda: a.raises(PubNubException, read, match='404'), what='object reports 404')


@step('get_all_uuid_metadata_builder', 'get_all_uuid_metadata_named', role='open')
def test_get_all_uuid_metadata(clients):
    pubnub = clients.sync('open', 'lister')
    kind = names.with_suffix('doc_type')
    users = [names.with_suffix('doc_user_' + x) for x in 'abc']
    record(uuids=users)
    try:
        for rank, uid in enumerate(users):
            pubnub.set_uuid_metadata(uuid=uid, name=kind, type='doc', custom={'rank': rank}).sync()

        def listed(page=None, **kwargs):
            # the named arguments of get_all_uuid_metadata have no page, only the builder does
            builder = pubnub.get_all_uuid_metadata(filter="name == '%s'" % kind, **kwargs)
            return (builder.page(page) if page else builder).sync().result

        eventually(lambda: a.eq(ids(listed().data), sorted(users), 'seeded users listed'), what='users listed')

        # snippet.get_all_uuid_metadata_builder
        # snippet.hide
        from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
        # snippet.show
        result = pubnub.get_all_uuid_metadata() \
            .include_custom(True) \
            .limit(10) \
            .filter("name == 'doc_type'") \
            .include_total_count(True) \
            .sort(PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)) \
            .page(None) \
            .sync()

        for uuid_data in result.result.data:
            print(f"UUID: {uuid_data['id']}")
            print(f"Name: {uuid_data['name']}")
            print(f"Custom: {uuid_data['custom']}")
        # snippet.end

        built = result.result
        a.eq(ids(built.data), users, 'ascending by id')
        a.eq(built.total_count, 3, 'total count')
        a.eq([u['custom'] for u in built.data], [{'rank': 0}, {'rank': 1}, {'rank': 2}])
        a.eq([u['name'] for u in built.data], [kind] * 3)

        # snippet.get_all_uuid_metadata_named
        metadata = pubnub.get_all_uuid_metadata(
            limit=10,
            include_custom=True,
            filter="name == 'doc_type'",
            include_total_count=True,
            sort_keys=[PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)]
        ).sync()

        for uuid_data in metadata.result.data:
            print(f"UUID: {uuid_data['id']}")
            print(f"Name: {uuid_data['name']}")
            print(f"Custom: {uuid_data['custom']}")
        # snippet.end

        a.eq(ids(metadata.result.data), users, 'named arguments: same list')
        a.eq(metadata.result.total_count, 3)
        a.eq([u['custom'] for u in metadata.result.data], [{'rank': 0}, {'rank': 1}, {'rank': 2}])

        # Defaults: custom and the total count are omitted, status and type are returned.
        plain = listed()
        a.not_contains(plain.data[0], 'custom', 'custom only when included')
        a.eq(plain.data[0]['type'], 'doc')
        a.contains(plain.data[0], 'status')
        a.eq(plain.total_count, None, 'total count only when requested')
        a.not_contains(listed(include_type=False).data[0], 'type', 'type can be left out')
        a.not_contains(listed(include_status=False).data[0], 'status', 'status can be left out')
        a.eq(ids(listed(sort_keys=[PNSortKey.desc(PNSortKeyValue.ID)]).data), list(reversed(users)), 'descending')
        only = pubnub.get_all_uuid_metadata(filter="name == '%s' && id == '%s'" % (kind, users[1])).sync()
        a.eq(ids(only.result.data), [users[1]], 'filter on name and id')

        # Paging with next and prev
        ordered = [PNSortKey.asc(PNSortKeyValue.ID)]
        first = listed(limit=2, sort_keys=ordered)
        a.eq(ids(first.data), users[:2])
        a.ok(isinstance(first.next, Next), 'next page token')
        a.eq(first.prev, None)
        second = listed(limit=2, sort_keys=ordered, page=first.next)
        a.eq(ids(second.data), users[2:])
        a.ok(isinstance(second.prev, Previous), 'prev page token')
        back = listed(limit=2, sort_keys=ordered, page=second.prev)
        a.eq(ids(back.data), users[:2], 'prev returns the first page')
    finally:
        cleanup(pubnub, users)


@step('get_uuid_metadata_builder', 'get_uuid_metadata_named', role='open')
def test_get_uuid_metadata(clients):
    pubnub = clients.sync('open', 'profile')
    me = pubnub.uuid
    other = names.with_suffix('doc_other')
    record(uuids=[me, other])
    try:
        pubnub.set_uuid_metadata(uuid=me, name='Doc profile', status='Active', type='doc',
                                 custom={'team': 'docs'}).sync()
        pubnub.set_uuid_metadata(uuid=other, name='Doc other', custom={'team': 'other'}).sync()

        # snippet.get_uuid_metadata_builder
        envelope = pubnub.get_uuid_metadata() \
            .include_custom(True) \
            .sync()
        # snippet.end

        data = envelope.result.data
        a.eq(data['id'], me, 'defaults to the configured user id')
        a.eq((data['name'], data['status'], data['type']), ('Doc profile', 'Active', 'doc'))
        a.eq(data['custom'], {'team': 'docs'})
        a.eq(envelope.result.status, 200)

        # snippet.get_uuid_metadata_named
        metadata = pubnub.get_uuid_metadata(include_custom=True).sync()
        # snippet.end

        a.eq(metadata.result.data, data, 'named arguments: same object')

        plain = pubnub.get_uuid_metadata().sync().result.data
        a.not_contains(plain, 'custom', 'custom only when included')
        a.not_contains(pubnub.get_uuid_metadata(include_type=False).sync().result.data, 'type')
        a.not_contains(pubnub.get_uuid_metadata(include_status=False).sync().result.data, 'status')
        explicit = pubnub.get_uuid_metadata(uuid=other, include_custom=True).sync().result.data
        a.eq((explicit['id'], explicit['custom']), (other, {'team': 'other'}), 'explicit uuid')
        missing = names.with_suffix('doc_missing')
        e = a.raises(PubNubException, lambda: pubnub.get_uuid_metadata(uuid=missing).sync(), match='404')
        a.contains(str(e), 'not found')
    finally:
        cleanup(pubnub, [me, other])


@step('set_uuid_metadata_builder', 'set_uuid_metadata_named', role='open', timeout=180)
def test_set_uuid_metadata(clients):
    pubnub = clients.sync('open', 'setter')
    first = names.with_suffix('some_uuid')
    second = names.with_suffix('some_uuid_named')
    record(uuids=[first, second])
    try:
        seen = watch(clients, first)

        # snippet.set_uuid_metadata_builder
        envelope = pubnub.set_uuid_metadata() \
            .include_custom(True) \
            .uuid("some_uuid") \
            .set_name("Some Name") \
            .set_status("Active") \
            .set_type("User") \
            .email("test@example.com") \
            .profile_url("http://example.com") \
            .external_id("1234567890") \
            .custom({"key1": "val1", "key2": "val2"}) \
            .sync()
        # snippet.end

        data = envelope.result.data
        a.eq({k: data[k] for k in UUID_FIELDS}, UUID_FIELDS)
        a.eq((data['id'], data['custom']), (first, {'key1': 'val1', 'key2': 'val2'}))
        a.ok(data['eTag'] and data['updated'], 'eTag and updated are returned')
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['id'], payload['name']), ('uuid', 'set', first, 'Some Name'))
        a.eq(payload['custom'], {'key1': 'val1', 'key2': 'val2'})
        a.eq(payload['eTag'], data['eTag'])
        read = pubnub.get_uuid_metadata(uuid=first, include_custom=True).sync().result.data
        a.eq(read, data, 'read back equals the set response')

        seen = watch(clients, second)

        # snippet.set_uuid_metadata_named
        envelope = pubnub.set_uuid_metadata(uuid="some_uuid_named",
                                            name="Some Name",
                                            status="Active", type="User",
                                            email="test@example.com",
                                            profile_url="http://example.com",
                                            external_id="1234567890",
                                            custom={"key1": "val1", "key2": "val2"},
                                            include_custom=True) \
            .sync()
        # snippet.end

        named = envelope.result.data
        a.eq({k: named[k] for k in UUID_FIELDS}, UUID_FIELDS)
        a.eq((named['id'], named['custom']), (second, {'key1': 'val1', 'key2': 'val2'}))
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['id']), ('uuid', 'set', second))

        # Custom is replaced as a whole, never merged
        replaced = pubnub.set_uuid_metadata(uuid=first, custom={'only': 'this'}, include_custom=True).sync().result.data
        a.eq(replaced['custom'], {'only': 'this'})
        read = pubnub.get_uuid_metadata(uuid=first, include_custom=True).sync().result.data
        a.eq(read['custom'], {'only': 'this'}, 'custom is overwritten')

        # Defaults of the include flags: status and type come back unless they are switched off
        light = pubnub.set_uuid_metadata(uuid=first, name='Some Name', include_status=False, include_type=False)
        light_data = light.sync().result.data
        a.not_contains(light_data, 'status')
        a.not_contains(light_data, 'type')
        a.not_contains(light_data, 'custom', 'custom only when included')

        # Setting the same data again triggers no event. The first event the watcher sees is the later change.
        fields = dict(name='Some Name', status='Active', type='User', custom={'only': 'this'})
        pubnub.set_uuid_metadata(uuid=first, **fields).sync()
        same = watch(clients, first)
        pubnub.set_uuid_metadata(uuid=first, **fields).sync()
        fields['name'] = 'Renamed'
        pubnub.set_uuid_metadata(uuid=first, **fields).sync()
        kind, event, payload = first_event(same)
        a.eq((event, payload['name']), ('set', 'Renamed'), 'unchanged data raised no event')
    finally:
        cleanup(pubnub, [first, second])


@step('remove_uuid_metadata_builder', 'remove_uuid_metadata_named', role='open')
def test_remove_uuid_metadata(clients):
    pubnub = clients.sync('open', 'remover')
    first = names.with_suffix('some_uuid')
    second = names.with_suffix('some_uuid_named')
    record(uuids=[first, second])
    try:
        for uid in (first, second):
            pubnub.set_uuid_metadata(uuid=uid, name='To remove', custom={'k': 'v'}).sync()
        a.eq(pubnub.get_uuid_metadata(uuid=first, include_custom=True).sync().result.data['custom'], {'k': 'v'})
        seen = watch(clients, first)

        # snippet.remove_uuid_metadata_builder
        envelope = pubnub.remove_uuid_metadata() \
            .uuid("some_uuid").sync()
        # snippet.end

        a.eq(envelope.result.status, 200)
        a.eq(envelope.result.data, None, 'nothing is returned')
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['id']), ('uuid', 'delete', first))
        gone(lambda: pubnub.get_uuid_metadata(uuid=first).sync())
        a.eq(pubnub.get_uuid_metadata(uuid=second).sync().result.data['id'], second, 'other users stay')

        # snippet.remove_uuid_metadata_named
        envelope = pubnub.remove_uuid_metadata(uuid="some_uuid_named").sync()
        # snippet.end

        a.eq(envelope.result.status, 200)
        gone(lambda: pubnub.get_uuid_metadata(uuid=second).sync())
        listed = pubnub.get_all_uuid_metadata(filter="id == '%s'" % second).sync().result.data
        a.eq(listed, [], 'the list no longer has the user')
    finally:
        cleanup(pubnub, [first, second])


@step('get_all_channel_metadata_builder', 'get_all_channel_metadata_named', role='open')
def test_get_all_channel_metadata(clients):
    pubnub = clients.sync('open', 'lister')
    kind = names.with_suffix('doc_type')
    channels = [names.with_suffix('doc_channel_' + x) for x in 'abc']
    record(channels=channels)
    try:
        for rank, channel in enumerate(channels):
            pubnub.set_channel_metadata(channel=channel, name=kind, type='doc', description='Channel %d' % rank,
                                        custom={'rank': rank}).sync()

        def listed(**kwargs):
            return pubnub.get_all_channel_metadata(filter="name == '%s'" % kind, **kwargs).sync().result

        eventually(lambda: a.eq(ids(listed().data), sorted(channels), 'seeded channels listed'), what='channels listed')

        # snippet.get_all_channel_metadata_builder
        # snippet.hide
        from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
        # snippet.show
        envelope = pubnub.get_all_channel_metadata() \
            .include_custom(True) \
            .limit(10) \
            .filter("name == 'doc_type'") \
            .include_total_count(True) \
            .sort(PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)) \
            .page(None) \
            .sync()
        # snippet.end

        built = envelope.result
        a.eq(ids(built.data), channels, 'ascending by id')
        a.eq(built.total_count, 3)
        a.eq([c['custom'] for c in built.data], [{'rank': 0}, {'rank': 1}, {'rank': 2}])
        a.eq([c['description'] for c in built.data], ['Channel 0', 'Channel 1', 'Channel 2'])

        # snippet.get_all_channel_metadata_named
        metadata = pubnub.get_all_channel_metadata(limit=10,
                                                   include_custom=True,
                                                   filter="name == 'doc_type'",
                                                   include_total_count=True,
                                                   sort_keys=[PNSortKey.asc(PNSortKeyValue.ID),
                                                              PNSortKey.desc(PNSortKeyValue.UPDATED)]) \
            .sync()
        # snippet.end

        a.eq(ids(metadata.result.data), channels, 'named arguments: same list')
        a.eq(metadata.result.total_count, 3)

        plain = listed()
        a.not_contains(plain.data[0], 'custom', 'custom only when included')
        a.eq(plain.data[0]['type'], 'doc')
        a.eq(plain.total_count, None)
        a.not_contains(listed(include_type=False).data[0], 'type')
        a.not_contains(listed(include_status=False).data[0], 'status')
        only = pubnub.get_all_channel_metadata(filter="name == '%s' && id == '%s'" % (kind, channels[2])).sync()
        a.eq(ids(only.result.data), [channels[2]], 'filter on name and id')

        ordered = [PNSortKey.asc(PNSortKeyValue.ID)]
        first = listed(limit=2, sort_keys=ordered)
        a.eq(ids(first.data), channels[:2])
        a.ok(isinstance(first.next, Next), 'next page token')
        second = listed(limit=2, sort_keys=ordered, page=first.next)
        a.eq(ids(second.data), channels[2:])
        a.ok(isinstance(second.prev, Previous), 'prev page token')
        a.eq(ids(listed(limit=2, sort_keys=ordered, page=second.prev).data), channels[:2])
    finally:
        cleanup(pubnub, channels=channels)


@step('get_channel_metadata_builder', 'get_channel_metadata_named', role='open')
def test_get_channel_metadata(clients):
    pubnub = clients.sync('open', 'reader')
    channel = names.with_suffix('channel_id')
    record(channels=[channel])
    try:
        pubnub.set_channel_metadata(channel=channel, name='Doc channel', description='About', status='live',
                                    type='room', custom={'topic': 'docs'}).sync()

        # snippet.get_channel_metadata_builder
        envelope = pubnub.get_channel_metadata() \
            .include_custom(True) \
            .channel("channel_id") \
            .sync()
        # snippet.end

        data = envelope.result.data
        a.eq((data['id'], data['name'], data['description']), (channel, 'Doc channel', 'About'))
        a.eq((data['status'], data['type'], data['custom']), ('live', 'room', {'topic': 'docs'}))
        a.eq(envelope.result.status, 200)

        # snippet.get_channel_metadata_named
        metadata = pubnub.get_channel_metadata(channel="channel_id", include_custom=True).sync()
        # snippet.end

        a.eq(metadata.result.data, data, 'named arguments: same object')
        a.not_contains(pubnub.get_channel_metadata(channel=channel).sync().result.data, 'custom')
        a.not_contains(pubnub.get_channel_metadata(channel=channel, include_type=False).sync().result.data, 'type')
        a.not_contains(pubnub.get_channel_metadata(channel=channel, include_status=False).sync().result.data, 'status')
        missing = names.with_suffix('doc_missing_channel')
        a.raises(PubNubException, lambda: pubnub.get_channel_metadata(channel=missing).sync(), match='404')
    finally:
        cleanup(pubnub, channels=[channel])


@step('set_channel_metadata_builder', 'set_channel_metadata_named', role='open', timeout=180)
def test_set_channel_metadata(clients):
    pubnub = clients.sync('open', 'setter')
    first = names.with_suffix('channel_id')
    second = names.with_suffix('channel_id_named')
    record(channels=[first, second])
    fields = {'name': 'Channel Name', 'description': 'Description', 'status': 'Archived', 'type': 'Archived'}
    try:
        seen = watch(clients, first)

        # snippet.set_channel_metadata_builder
        envelope = pubnub.set_channel_metadata() \
            .include_custom(True) \
            .channel("channel_id") \
            .set_name("Channel Name") \
            .set_status("Archived") \
            .set_type("Archived") \
            .description("Description") \
            .custom({"key1": "val1", "key2": "val2"}) \
            .sync()
        # snippet.end

        data = envelope.result.data
        a.eq({k: data[k] for k in fields}, fields)
        a.eq((data['id'], data['custom']), (first, {'key1': 'val1', 'key2': 'val2'}))
        a.ok(data['eTag'] and data['updated'], 'eTag and updated are returned')
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['id'], payload['name']), ('channel', 'set', first, 'Channel Name'))
        a.eq(payload['custom'], {'key1': 'val1', 'key2': 'val2'})
        read = pubnub.get_channel_metadata(channel=first, include_custom=True).sync().result.data
        a.eq(read, data, 'read back equals the set response')

        seen = watch(clients, second)

        # snippet.set_channel_metadata_named
        envelope = pubnub.set_channel_metadata(channel="channel_id_named",
                                               name="Channel Name",
                                               status="Archived",
                                               type="Archived",
                                               description="Description",
                                               custom={"key1": "val1", "key2": "val2"},
                                               include_custom=True) \
            .sync()
        # snippet.end

        named = envelope.result.data
        a.eq({k: named[k] for k in fields}, fields)
        a.eq((named['id'], named['custom']), (second, {'key1': 'val1', 'key2': 'val2'}))
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['id']), ('channel', 'set', second))

        replaced = pubnub.set_channel_metadata(channel=first, custom={'only': 'this'},
                                               include_custom=True).sync().result.data
        a.eq(replaced['custom'], {'only': 'this'})
        read = pubnub.get_channel_metadata(channel=first, include_custom=True).sync().result.data
        a.eq(read['custom'], {'only': 'this'}, 'custom is overwritten')
        light = pubnub.set_channel_metadata(channel=first, name='Channel Name', include_status=False,
                                            include_type=False).sync().result.data
        a.not_contains(light, 'status')
        a.not_contains(light, 'type')
        a.not_contains(light, 'custom', 'custom only when included')

        keep = dict(name='Channel Name', description='Description', status='Archived', type='Archived',
                    custom={'only': 'this'})
        pubnub.set_channel_metadata(channel=first, **keep).sync()
        same = watch(clients, first)
        pubnub.set_channel_metadata(channel=first, **keep).sync()
        keep['description'] = 'Changed'
        pubnub.set_channel_metadata(channel=first, **keep).sync()
        kind, event, payload = first_event(same)
        a.eq((event, payload['description']), ('set', 'Changed'), 'unchanged data raised no event')
    finally:
        cleanup(pubnub, channels=[first, second])


@step('remove_channel_metadata_builder', 'remove_channel_metadata_named', role='open')
def test_remove_channel_metadata(clients):
    pubnub = clients.sync('open', 'remover')
    first = names.with_suffix('channel_id')
    second = names.with_suffix('channel_id_named')
    record(channels=[first, second])
    try:
        for channel in (first, second):
            pubnub.set_channel_metadata(channel=channel, name='To remove').sync()
        seen = watch(clients, first)

        # snippet.remove_channel_metadata_builder
        envelope = pubnub.remove_channel_metadata() \
            .channel("channel_id") \
            .sync()
        # snippet.end

        a.eq(envelope.result.status, 200)
        a.eq(envelope.result.data, None, 'nothing is returned')
        kind, event, payload = first_event(seen)
        a.eq((kind, event, payload['id']), ('channel', 'delete', first))
        gone(lambda: pubnub.get_channel_metadata(channel=first).sync())
        a.eq(pubnub.get_channel_metadata(channel=second).sync().result.data['id'], second, 'other channels stay')

        # snippet.remove_channel_metadata_named
        envelope = pubnub.remove_channel_metadata(channel="channel_id_named").sync()
        # snippet.end

        a.eq(envelope.result.status, 200)
        gone(lambda: pubnub.get_channel_metadata(channel=second).sync())
        listed = pubnub.get_all_channel_metadata(filter="id == '%s'" % second).sync().result.data
        a.eq(listed, [], 'the list no longer has the channel')
    finally:
        cleanup(pubnub, channels=[first, second])
