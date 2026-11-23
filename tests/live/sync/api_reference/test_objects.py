"""Docs page: App Context (sync). User and channel metadata.

Also channel memberships, channel members and the PNChannelMembership and PNUUID classes, because they are on the
same docs page. The helpers are in shared/objects.py. Every object a test creates is removed in a finally block, and
the janitor cleans the names listed in NAMES.
"""
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
from pubnub.models.consumer.objects_v2.page import Next, Previous
from pubnub.models.consumer.objects_v2.common import MemberIncludes, MembershipIncludes
from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
import pytest

from support import assertions as a
from support.wait import settled
from shared.objects import (
    CUSTOM_1, CUSTOM_2, UUID_FIELDS, attempt, by_channel, by_member, channel_ids, check_members, check_memberships,
    cleanup, first_event, fresh, gone, ids, member_ids, record, seed_channels, seed_members, seed_memberships,
    seed_one_member, seed_one_membership, seed_users, settled_read, watch,
)

# Every read after a write waits for consecutive agreeing reads (settled), and a test that asserts exact lists first
# removes the leftovers of both sides (fresh). Both cost time, so the default timeout of pytest.ini is too short.
pytestmark = pytest.mark.timeout(240)


def memberships_of(pubnub, uid, **kwargs):
    return attempt(lambda: pubnub.get_memberships(uuid=uid, **kwargs).sync()).result.data


def members_of(pubnub, channel, **kwargs):
    return attempt(lambda: pubnub.get_channel_members(channel=channel, **kwargs).sync()).result.data


def memberships_visible(pubnub, uid, plain, with_custom):
    """Precondition: the seeded memberships with all details, on consecutive reads. A module-level helper, because
    the samples import MembershipIncludes themselves, which makes the name local to the whole test function."""
    settled_read(lambda: pubnub.get_memberships(uuid=uid, include=MembershipIncludes(
        custom=True, channel=True, channel_custom=True)).sync(),
        lambda e: check_memberships(e.result.data, plain, with_custom), 'seeded memberships visible')


def members_visible(pubnub, channel, plain, with_custom):
    """Precondition: the seeded members with all details, on consecutive reads (see memberships_visible)."""
    settled_read(lambda: pubnub.get_channel_members(channel=channel, include=MemberIncludes(
        custom=True, user=True, user_custom=True)).sync(),
        lambda e: check_members(e.result.data, plain, with_custom), 'seeded members visible')


def settled_eq(read, want, what):
    """read() equals want on consecutive reads (a write is visible on every replica)."""
    settled(lambda: a.eq(read(), want, what), timeout=30, what=what)


def test_get_all_uuid_metadata_builder(clients):
    """Snippets: get_all_uuid_metadata_builder, get_all_uuid_metadata_named."""
    pubnub = clients.sync('open', 'lister')
    kind = 'doc_type'
    users = [('doc_user_' + x) for x in 'abc']
    record(uuids=users)
    try:
        for rank, uid in enumerate(users):
            pubnub.set_uuid_metadata(uuid=uid, name=kind, type='doc', custom={'rank': rank}).sync()

        def listed(page=None, **kwargs):
            # the named arguments of get_all_uuid_metadata have no page, only the builder does
            builder = pubnub.get_all_uuid_metadata(filter="name == '%s'" % kind, **kwargs)
            return (builder.page(page) if page else builder).sync().result

        settled_eq(lambda: ids(attempt(listed).data), sorted(users), 'seeded users listed')

        # snippet.get_all_uuid_metadata_builder
        from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
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
        from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue

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


def test_get_uuid_metadata_builder(clients):
    """Snippets: get_uuid_metadata_builder, get_uuid_metadata_named."""
    pubnub = clients.sync('open', 'profile')
    me = pubnub.uuid
    other = 'doc_other'
    record(uuids=[me, other])
    try:
        pubnub.set_uuid_metadata(uuid=me, name='Doc profile', status='Active', type='doc',
                                 custom={'team': 'docs'}).sync()
        pubnub.set_uuid_metadata(uuid=other, name='Doc other', custom={'team': 'other'}).sync()
        settled_eq(lambda: attempt(lambda: pubnub.get_uuid_metadata(uuid=me, include_custom=True).sync())
                   .result.data['custom'], {'team': 'docs'}, 'profile visible')
        settled_eq(lambda: attempt(lambda: pubnub.get_uuid_metadata(uuid=other, include_custom=True).sync())
                   .result.data['custom'], {'team': 'other'}, 'other profile visible')

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
        missing = 'doc_missing'
        e = a.raises(PubNubException, lambda: pubnub.get_uuid_metadata(uuid=missing).sync(), match='404')
        a.contains(str(e), 'not found')
    finally:
        cleanup(pubnub, [me, other])


@pytest.mark.timeout(300)
def test_set_uuid_metadata_builder(clients):
    """Snippets: set_uuid_metadata_builder, set_uuid_metadata_named."""
    pubnub = clients.sync('open', 'setter')
    first = 'some_uuid'
    second = 'some_uuid_named'
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
        settled_eq(lambda: attempt(lambda: pubnub.get_uuid_metadata(uuid=first, include_custom=True).sync())
                   .result.data, data, 'read back equals the set response')

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
        settled_eq(lambda: attempt(lambda: pubnub.get_uuid_metadata(uuid=first, include_custom=True).sync())
                   .result.data['custom'], {'only': 'this'}, 'custom is overwritten')

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


def test_remove_uuid_metadata_builder(clients):
    """Snippets: remove_uuid_metadata_builder, remove_uuid_metadata_named."""
    pubnub = clients.sync('open', 'remover')
    first = 'some_uuid'
    second = 'some_uuid_named'
    record(uuids=[first, second])
    try:
        for uid in (first, second):
            pubnub.set_uuid_metadata(uuid=uid, name='To remove', custom={'k': 'v'}).sync()
        for uid in (first, second):
            settled_eq(lambda: attempt(lambda: pubnub.get_uuid_metadata(uuid=uid, include_custom=True).sync())
                       .result.data['custom'], {'k': 'v'}, f'{uid} visible')
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
        settled_eq(lambda: attempt(lambda: pubnub.get_uuid_metadata(uuid=second).sync()).result.data['id'], second,
                   'other users stay')

        # snippet.remove_uuid_metadata_named
        envelope = pubnub.remove_uuid_metadata(uuid="some_uuid_named").sync()
        # snippet.end

        a.eq(envelope.result.status, 200)
        gone(lambda: pubnub.get_uuid_metadata(uuid=second).sync())
        settled_eq(lambda: pubnub.get_all_uuid_metadata(filter="id == '%s'" % second).sync().result.data, [],
                   'the list no longer has the user')
    finally:
        cleanup(pubnub, [first, second])


def test_get_all_channel_metadata_builder(clients):
    """Snippets: get_all_channel_metadata_builder, get_all_channel_metadata_named."""
    pubnub = clients.sync('open', 'lister')
    kind = 'doc_type'
    channels = [('doc_channel_' + x) for x in 'abc']
    record(channels=channels)
    try:
        for rank, channel in enumerate(channels):
            pubnub.set_channel_metadata(channel=channel, name=kind, type='doc', description='Channel %d' % rank,
                                        custom={'rank': rank}).sync()

        def listed(**kwargs):
            return pubnub.get_all_channel_metadata(filter="name == '%s'" % kind, **kwargs).sync().result

        settled_eq(lambda: ids(attempt(listed).data), sorted(channels), 'seeded channels listed')

        # snippet.get_all_channel_metadata_builder
        from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
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
        from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue

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


def test_get_channel_metadata_builder(clients):
    """Snippets: get_channel_metadata_builder, get_channel_metadata_named."""
    pubnub = clients.sync('open', 'reader')
    channel = 'channel_id'
    record(channels=[channel])
    try:
        pubnub.set_channel_metadata(channel=channel, name='Doc channel', description='About', status='live',
                                    type='room', custom={'topic': 'docs'}).sync()
        settled_eq(lambda: attempt(lambda: pubnub.get_channel_metadata(channel=channel, include_custom=True).sync())
                   .result.data['custom'], {'topic': 'docs'}, 'channel visible')

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
        missing = 'doc_missing_channel'
        a.raises(PubNubException, lambda: pubnub.get_channel_metadata(channel=missing).sync(), match='404')
    finally:
        cleanup(pubnub, channels=[channel])


@pytest.mark.timeout(300)
def test_set_channel_metadata_builder(clients):
    """Snippets: set_channel_metadata_builder, set_channel_metadata_named."""
    pubnub = clients.sync('open', 'setter')
    first = 'channel_id'
    second = 'channel_id_named'
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
        settled_eq(lambda: attempt(lambda: pubnub.get_channel_metadata(channel=first, include_custom=True).sync())
                   .result.data, data, 'read back equals the set response')

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
        settled_eq(lambda: attempt(lambda: pubnub.get_channel_metadata(channel=first, include_custom=True).sync())
                   .result.data['custom'], {'only': 'this'}, 'custom is overwritten')
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


def test_remove_channel_metadata_builder(clients):
    """Snippets: remove_channel_metadata_builder, remove_channel_metadata_named."""
    pubnub = clients.sync('open', 'remover')
    first = 'channel_id'
    second = 'channel_id_named'
    record(channels=[first, second])
    try:
        for channel in (first, second):
            pubnub.set_channel_metadata(channel=channel, name='To remove').sync()
        for channel in (first, second):
            settled_eq(lambda: attempt(lambda: pubnub.get_channel_metadata(channel=channel).sync()).result.data['name'],
                       'To remove', f'{channel} visible')
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
        settled_eq(lambda: attempt(lambda: pubnub.get_channel_metadata(channel=second).sync()).result.data['id'],
                   second, 'other channels stay')

        # snippet.remove_channel_metadata_named
        envelope = pubnub.remove_channel_metadata(channel="channel_id_named").sync()
        # snippet.end

        a.eq(envelope.result.status, 200)
        gone(lambda: pubnub.get_channel_metadata(channel=second).sync())
        settled_eq(lambda: pubnub.get_all_channel_metadata(filter="id == '%s'" % second).sync().result.data, [],
                   'the list no longer has the channel')
    finally:
        cleanup(pubnub, channels=[first, second])


def test_get_memberships_builder(clients):
    """Snippets: get_memberships_builder, get_memberships_named."""
    pubnub = clients.sync('open', 'reader')
    uid = 'some_uuid'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([uid], [plain, with_custom])
    try:
        fresh(pubnub, [uid], [plain, with_custom])
        seed_channels(pubnub, plain, with_custom)
        seed_memberships(pubnub, uid, plain, with_custom)
        memberships_visible(pubnub, uid, plain, with_custom)

        # snippet.get_memberships_builder
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        envelope = pubnub.get_memberships() \
            .include(MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .uuid("some_uuid").sync()
        # snippet.end

        check_memberships(envelope.result.data, plain, with_custom)
        a.eq(envelope.result.status, 200)

        # snippet.get_memberships_named
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes

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
        settled_eq(lambda: [(m['type'], m['status']) for m in memberships_of(
            pubnub, uid, include=MembershipIncludes(type=True, status=True)) if m['channel']['id'] == plain],
            [('doc', 'active')], 'type and status of the membership')

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


@pytest.mark.timeout(300)
def test_set_memberships_builder(clients):
    """Snippets: set_memberships_builder, set_memberships_named."""
    pubnub = clients.sync('open', 'setter')
    first = 'some_uuid'
    second = 'some_uuid_named'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([first, second], [plain, with_custom])
    try:
        fresh(pubnub, [first, second], [plain, with_custom])
        seen = watch(clients, first)

        # snippet.set_memberships_builder
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
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
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership

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
        settled_eq(lambda: sorted(member_ids(members_of(pubnub, plain))), sorted([first, second]),
                   'both users are members')

        # Set adds to the stored memberships, it does not replace them
        extra = 'somechannel_extra'
        record(channels=[extra])
        try:
            pubnub.set_channel_metadata(channel=extra, name='extra').sync()
            added = pubnub.set_memberships(uuid=first, channel_memberships=[PNChannelMembership.channel(extra)]).sync()
            a.eq(sorted(channel_ids(added.result.data)), sorted([plain, with_custom, extra]), 'set keeps the others')
        finally:
            cleanup(pubnub, [first], [extra])
    finally:
        cleanup(pubnub, [first, second], [plain, with_custom])


@pytest.mark.timeout(300)
def test_remove_memberships_builder(clients):
    """Snippets: remove_memberships_builder, remove_memberships_named."""
    pubnub = clients.sync('open', 'remover')
    first = 'some_uuid'
    second = 'some_uuid_named'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([first, second], [plain, with_custom])
    try:
        fresh(pubnub, [first, second], [plain, with_custom])
        seed_channels(pubnub, plain, with_custom)
        for uid in (first, second):
            seed_memberships(pubnub, uid, plain, with_custom)
        for uid in (first, second):
            settled_eq(lambda: sorted(channel_ids(memberships_of(pubnub, uid))), sorted([plain, with_custom]),
                       f'memberships of {uid} seeded')
        seen = watch(clients, first)

        # snippet.remove_memberships_builder
        from pubnub.endpoints.objects_v2.objects_endpoint import ChannelIncludeEndpoint
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
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
        settled_eq(lambda: channel_ids(memberships_of(pubnub, first)), [with_custom], 'membership removed')
        settled_eq(lambda: len(memberships_of(pubnub, second)), 2, 'other users keep theirs')

        # snippet.remove_memberships_named
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership

        envelope = pubnub.remove_memberships(uuid="some_uuid_named",
                                             channel_memberships=[PNChannelMembership.channel(some_channel)],
                                             include=MembershipIncludes(custom=True, channel=True,
                                                                        channel_custom=True)) \
            .sync()
        # snippet.end

        a.eq(channel_ids(envelope.result.data), [with_custom])
        a.eq(envelope.result.data[0]['channel']['custom'], CUSTOM_1)
        settled_eq(lambda: channel_ids(memberships_of(pubnub, second)), [with_custom], 'second membership removed')
        settled_eq(lambda: attempt(lambda: pubnub.get_channel_metadata(channel=plain).sync()).result.data['id'], plain,
                   'the channel stays')
    finally:
        cleanup(pubnub, [first, second], [plain, with_custom])


@pytest.mark.timeout(300)
def test_manage_memberships_builder(clients):
    """Snippets: manage_memberships_builder, manage_memberships_named."""
    pubnub = clients.sync('open', 'manager')
    first = 'some_uuid'
    second = 'some_uuid_named'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([first, second], [plain, with_custom])
    try:
        fresh(pubnub, [first, second], [plain, with_custom])
        seed_channels(pubnub, plain, with_custom)
        for uid in (first, second):
            seed_one_membership(pubnub, uid, with_custom)
        for uid in (first, second):
            settled_eq(lambda: channel_ids(memberships_of(pubnub, uid)), [with_custom], f'seed of {uid} visible')
        seen = watch(clients, first)

        # snippet.manage_memberships_builder
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
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
        settled_eq(lambda: channel_ids(memberships_of(pubnub, first)), [plain], 'memberships changed')

        # snippet.manage_memberships_named
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership

        envelope = pubnub.manage_memberships(uuid="some_uuid_named",
                                             channel_memberships_to_set=[PNChannelMembership.channel(some_channel)],
                                             channel_memberships_to_remove=[
                                                 PNChannelMembership.channel(some_channel_with_custom)],
                                             include=MembershipIncludes(custom=True, channel=True,
                                                                        channel_custom=True)) \
            .sync()
        # snippet.end

        a.eq(channel_ids(envelope.result.data), [plain])
        settled_eq(lambda: channel_ids(memberships_of(pubnub, second)), [plain], 'second user changed')
    finally:
        cleanup(pubnub, [first, second], [plain, with_custom])


def test_get_channel_members_builder(clients):
    """Snippets: get_channel_members_builder, get_channel_members_named."""
    pubnub = clients.sync('open', 'reader')
    channel = 'channel_id'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [channel])
    try:
        fresh(pubnub, [plain, with_custom], [channel])
        seed_users(pubnub, plain, with_custom)
        pubnub.set_channel_metadata(channel=channel, name='Doc channel').sync()
        seed_members(pubnub, channel, plain, with_custom)
        members_visible(pubnub, channel, plain, with_custom)

        # snippet.get_channel_members_builder
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        envelope = pubnub.get_channel_members() \
            .channel("channel_id") \
            .include(MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        check_members(envelope.result.data, plain, with_custom)
        a.eq(envelope.result.status, 200)

        # snippet.get_channel_members_named
        from pubnub.models.consumer.objects_v2.common import MemberIncludes

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


@pytest.mark.timeout(300)
def test_set_channel_members_builder(clients):
    """Snippets: set_channel_members_builder, set_channel_members_named."""
    pubnub = clients.sync('open', 'setter')
    first = 'channel_id'
    second = 'channel_id_named'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [first, second])
    try:
        fresh(pubnub, [plain, with_custom, 'some_uuid_extra'], [first, second])
        seen = watch(clients, first)

        # snippet.set_channel_members_builder
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
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
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID

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

        settled_eq(lambda: sorted(channel_ids(memberships_of(pubnub, plain))), sorted([first, second]),
                   'the user side sees both channels')

        # Set adds to the stored members, it does not replace them
        extra = 'some_uuid_extra'
        record(uuids=[extra])
        try:
            pubnub.set_uuid_metadata(uuid=extra, name='extra').sync()
            added = pubnub.set_channel_members(channel=first, uuids=[PNUUID.uuid(extra)]).sync()
            a.eq(sorted(member_ids(added.result.data)), sorted([plain, with_custom, extra]), 'set keeps the others')
        finally:
            cleanup(pubnub, [extra], [])
    finally:
        cleanup(pubnub, [plain, with_custom], [first, second])


@pytest.mark.timeout(300)
def test_remove_channel_members_builder(clients):
    """Snippets: remove_channel_members_builder, remove_channel_members_named."""
    pubnub = clients.sync('open', 'remover')
    first = 'channel_id'
    second = 'channel_id_named'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [first, second])
    try:
        fresh(pubnub, [plain, with_custom, 'some_uuid_extra'], [first, second])
        seed_users(pubnub, plain, with_custom)
        for channel in (first, second):
            pubnub.set_channel_metadata(channel=channel, name='Doc channel').sync()
            seed_members(pubnub, channel, plain, with_custom)
        for channel in (first, second):
            settled_eq(lambda: sorted(member_ids(members_of(pubnub, channel))), sorted([plain, with_custom]),
                       f'members of {channel} seeded')
        seen = watch(clients, first)

        # snippet.remove_channel_members_builder
        from pubnub.endpoints.objects_v2.objects_endpoint import UUIDIncludeEndpoint
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID
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
        settled_eq(lambda: member_ids(members_of(pubnub, first)), [with_custom], 'member removed')
        settled_eq(lambda: len(members_of(pubnub, second)), 2, 'other channels keep theirs')

        # snippet.remove_channel_members_named
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID

        envelope = pubnub.remove_channel_members(channel="channel_id_named",
                                                 uuids=[PNUUID.uuid("some_uuid")],
                                                 include=MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        a.eq(member_ids(envelope.result.data), [with_custom])
        a.eq(envelope.result.data[0]['uuid']['custom'], CUSTOM_1)
        settled_eq(lambda: member_ids(members_of(pubnub, second)), [with_custom], 'second member removed')
        settled_eq(lambda: attempt(lambda: pubnub.get_uuid_metadata(uuid=plain).sync()).result.data['id'], plain,
                   'the user stays')
    finally:
        cleanup(pubnub, [plain, with_custom], [first, second])


@pytest.mark.timeout(300)
def test_manage_channel_members_builder(clients):
    """Snippets: manage_channel_members_builder, manage_channel_members_named."""
    pubnub = clients.sync('open', 'manager')
    first = 'channel_id'
    second = 'channel_id_named'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [first, second])
    try:
        fresh(pubnub, [plain, with_custom, 'some_uuid_extra'], [first, second])
        seed_users(pubnub, plain, with_custom)
        for channel in (first, second):
            pubnub.set_channel_metadata(channel=channel, name='Doc channel').sync()
            seed_one_member(pubnub, channel, with_custom)
        for channel in (first, second):
            settled_eq(lambda: member_ids(members_of(pubnub, channel)), [with_custom], f'seed of {channel} visible')
        seen = watch(clients, first)

        # snippet.manage_channel_members_builder
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
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
        settled_eq(lambda: member_ids(members_of(pubnub, first)), [plain], 'members changed')

        # snippet.manage_channel_members_named
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID

        envelope = pubnub.manage_channel_members(channel="channel_id_named",
                                                 uuids_to_set=[PNUUID.uuid("some_uuid")],
                                                 uuids_to_remove=[PNUUID.uuid("some_uuid_with_custom")],
                                                 include=MemberIncludes(custom=True, user=True, user_custom=True)) \
            .sync()
        # snippet.end

        a.eq(member_ids(envelope.result.data), [plain])
        settled_eq(lambda: member_ids(members_of(pubnub, second)), [plain], 'second channel changed')
    finally:
        cleanup(pubnub, [plain, with_custom], [first, second])


def test_pnchannelmembership_class(clients):
    """Snippet: pnchannelmembership_class."""
    pubnub = clients.sync('open', 'classes')
    uid = 'some_uuid'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([uid], [plain, with_custom])
    try:
        fresh(pubnub, [uid], [plain, with_custom, 'channel_id'])
        seed_channels(pubnub, plain, with_custom)

        # snippet.pnchannelmembership_class
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
        membership = PNChannelMembership.channel("somechannel")
        membership_with_custom = PNChannelMembership.channel_with_custom("somechannel_with_custom",
                                                                         {"key5": "val1", "key6": "val2"})
        # snippet.end

        a.eq(type(membership).__name__, 'JustChannel')
        a.eq(type(membership_with_custom).__name__, 'ChannelWithCustom')
        a.eq(membership.to_payload_dict(), {'channel': {'id': plain}})
        a.eq(membership_with_custom.to_payload_dict(), {'channel': {'id': with_custom}, 'custom': CUSTOM_2})
        pubnub.set_memberships(uuid=uid, channel_memberships=[membership, membership_with_custom]).sync()
        settled_eq(lambda: {m['channel']['id']: m['custom'] for m in memberships_of(
            pubnub, uid, include=MembershipIncludes(custom=True))}, {plain: None, with_custom: CUSTOM_2},
            'memberships set from the helper objects')
    finally:
        cleanup(pubnub, [uid], [plain, with_custom])


def test_pnuuid_class(clients):
    """Snippet: pnuuid_class."""
    pubnub = clients.sync('open', 'classes')
    channel = 'channel_id'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [channel])
    try:
        fresh(pubnub, [plain, with_custom, 'some_uuid_extra'], [channel])
        seed_users(pubnub, plain, with_custom)
        pubnub.set_channel_metadata(channel=channel, name='Doc channel').sync()

        # snippet.pnuuid_class
        from pubnub.models.consumer.objects_v2.channel_members import PNUUID
        member = PNUUID.uuid("some_uuid")
        member_with_custom = PNUUID.uuid_with_custom("some_uuid_with_custom", {"key5": "val1", "key6": "val2"})
        # snippet.end

        a.eq(type(member).__name__, 'JustUUID')
        a.eq(type(member_with_custom).__name__, 'UUIDWithCustom')
        a.eq(member.to_payload_dict(), {'uuid': {'id': plain}})
        a.eq(member_with_custom.to_payload_dict(), {'uuid': {'id': with_custom}, 'custom': CUSTOM_2})
        pubnub.set_channel_members(channel=channel, uuids=[member, member_with_custom]).sync()
        settled_eq(lambda: {m['uuid']['id']: m['custom'] for m in members_of(
            pubnub, channel, include=MemberIncludes(custom=True))}, {plain: None, with_custom: CUSTOM_2},
            'members set from the helper objects')
    finally:
        cleanup(pubnub, [plain, with_custom], [channel])
