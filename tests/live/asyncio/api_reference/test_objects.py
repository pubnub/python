"""Docs page: App Context (asyncio). User and channel metadata.

Also channel memberships, channel members and the PNChannelMembership and PNUUID classes, because they are on the
same docs page. Same steps as sync/api_reference/test_objects.py with await. The helpers are in shared/objects.py. Every
object a test creates is removed in a finally block, and the janitor cleans the names listed in NAMES. The asyncio
client does not raise on an HTTP error, future() resolves with a PubNubAsyncioException, so the reads outside the
snippets go through attempt() and checked().
"""
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
from pubnub.models.consumer.objects_v2.page import Next, Previous
from pubnub.models.consumer.objects_v2.common import MemberIncludes, MembershipIncludes
from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
import pytest

from support import assertions as a
from support.wait import asettled
from shared.objects import (
    CUSTOM_1, CUSTOM_2, UUID_FIELDS, attempt_async as attempt, by_channel, by_member, channel_ids, check_members,
    check_memberships, checked, cleanup_async as cleanup, expect_error_async, first_event_async as first_event,
    fresh_async as fresh, gone_async as gone, ids, member_ids, record, seed_channels_async as seed_channels,
    seed_members_async as seed_members, seed_memberships_async as seed_memberships,
    seed_one_member_async as seed_one_member, seed_one_membership_async as seed_one_membership,
    seed_users_async as seed_users, settled_read_async as settled_read, watch_async as watch,
)

# Every read after a write waits for consecutive agreeing reads (settled), and a test that asserts exact lists first
# removes the leftovers of both sides (fresh). Both cost time, so the default timeout of pytest.ini is too short.
pytestmark = pytest.mark.timeout(240)


async def memberships_of(pubnub, uid, **kwargs):
    return (await attempt(lambda: pubnub.get_memberships(uuid=uid, **kwargs).future())).result.data


async def members_of(pubnub, channel, **kwargs):
    return (await attempt(lambda: pubnub.get_channel_members(channel=channel, **kwargs).future())).result.data


async def uuid_data(pubnub, uid, **kwargs):
    return (await attempt(lambda: pubnub.get_uuid_metadata(uuid=uid, **kwargs).future())).result.data


async def channel_data(pubnub, channel, **kwargs):
    return (await attempt(lambda: pubnub.get_channel_metadata(channel=channel, **kwargs).future())).result.data


async def channels_of(pubnub, uid, **kwargs):
    return channel_ids(await memberships_of(pubnub, uid, **kwargs))


async def users_of(pubnub, channel, **kwargs):
    return member_ids(await members_of(pubnub, channel, **kwargs))


async def sorted_of(values):
    return sorted(await values)


async def memberships_visible(pubnub, uid, plain, with_custom):
    """Precondition: the seeded memberships with all details, on consecutive reads. A module-level helper, because
    the samples import MembershipIncludes themselves, which makes the name local to the whole test function."""
    await settled_read(lambda: pubnub.get_memberships(uuid=uid, include=MembershipIncludes(
        custom=True, channel=True, channel_custom=True)).future(),
        lambda e: check_memberships(e.result.data, plain, with_custom), 'seeded memberships visible')


async def members_visible(pubnub, channel, plain, with_custom):
    """Precondition: the seeded members with all details, on consecutive reads (see memberships_visible)."""
    await settled_read(lambda: pubnub.get_channel_members(channel=channel, include=MemberIncludes(
        custom=True, user=True, user_custom=True)).future(),
        lambda e: check_members(e.result.data, plain, with_custom), 'seeded members visible')


async def settled_eq(read, want, what):
    """read() (a coroutine function) equals want on consecutive reads (a write is visible on every replica)."""
    async def once():
        a.eq(await read(), want, what)
    await asettled(once, timeout=30, what=what)


async def test_get_all_uuid_metadata_builder(aclients):
    """Snippets: get_all_uuid_metadata_builder, get_all_uuid_metadata_named."""
    pubnub = aclients.asyncio('open', 'lister')
    kind = 'doc_type'
    users = [('doc_user_' + x) for x in 'abc']
    record(uuids=users)
    try:
        for rank, uid in enumerate(users):
            checked(await pubnub.set_uuid_metadata(uuid=uid, name=kind, type='doc', custom={'rank': rank}).future())

        async def listed(page=None, **kwargs):
            # the named arguments of get_all_uuid_metadata have no page, only the builder does
            builder = pubnub.get_all_uuid_metadata(filter="name == '%s'" % kind, **kwargs)
            return (await attempt(lambda: (builder.page(page) if page else builder).future())).result

        async def listed_ids():
            return ids((await listed()).data)

        await settled_eq(listed_ids, sorted(users), 'seeded users listed')

        # snippet.get_all_uuid_metadata_builder
        from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
        result = await pubnub.get_all_uuid_metadata(include_custom=True, include_total_count=True) \
            .limit(10) \
            .filter("name == 'doc_type'") \
            .sort(PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)) \
            .page(None) \
            .future()

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

        metadata = await pubnub.get_all_uuid_metadata(
            limit=10,
            include_custom=True,
            filter="name == 'doc_type'",
            include_total_count=True,
            sort_keys=[PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)]
        ).future()

        for uuid_data in metadata.result.data:
            print(f"UUID: {uuid_data['id']}")
            print(f"Name: {uuid_data['name']}")
            print(f"Custom: {uuid_data['custom']}")
        # snippet.end

        a.eq(ids(metadata.result.data), users, 'named arguments: same list')
        a.eq(metadata.result.total_count, 3)
        a.eq([u['custom'] for u in metadata.result.data], [{'rank': 0}, {'rank': 1}, {'rank': 2}])

        # Defaults: custom and the total count are omitted, status and type are returned.
        plain = await listed()
        a.not_contains(plain.data[0], 'custom', 'custom only when included')
        a.eq(plain.data[0]['type'], 'doc')
        a.contains(plain.data[0], 'status')
        a.eq(plain.total_count, None, 'total count only when requested')
        a.not_contains((await listed(include_type=False)).data[0], 'type', 'type can be left out')
        a.not_contains((await listed(include_status=False)).data[0], 'status', 'status can be left out')
        a.eq(ids((await listed(sort_keys=[PNSortKey.desc(PNSortKeyValue.ID)])).data), list(reversed(users)),
             'descending')
        only = checked(await pubnub.get_all_uuid_metadata(
            filter="name == '%s' && id == '%s'" % (kind, users[1])).future())
        a.eq(ids(only.result.data), [users[1]], 'filter on name and id')

        # Paging with next and prev
        ordered = [PNSortKey.asc(PNSortKeyValue.ID)]
        first = await listed(limit=2, sort_keys=ordered)
        a.eq(ids(first.data), users[:2])
        a.ok(isinstance(first.next, Next), 'next page token')
        a.eq(first.prev, None)
        second = await listed(limit=2, sort_keys=ordered, page=first.next)
        a.eq(ids(second.data), users[2:])
        a.ok(isinstance(second.prev, Previous), 'prev page token')
        back = await listed(limit=2, sort_keys=ordered, page=second.prev)
        a.eq(ids(back.data), users[:2], 'prev returns the first page')
    finally:
        await cleanup(pubnub, users)


async def test_get_uuid_metadata_builder(aclients):
    """Snippets: get_uuid_metadata_builder, get_uuid_metadata_named."""
    pubnub = aclients.asyncio('open', 'profile')
    me = pubnub.uuid
    other = 'doc_other'
    record(uuids=[me, other])
    try:
        checked(await pubnub.set_uuid_metadata(uuid=me, name='Doc profile', status='Active', type='doc',
                                               custom={'team': 'docs'}).future())
        checked(await pubnub.set_uuid_metadata(uuid=other, name='Doc other', custom={'team': 'other'}).future())

        async def my_custom():
            return (await uuid_data(pubnub, me, include_custom=True))['custom']

        async def other_custom():
            return (await uuid_data(pubnub, other, include_custom=True))['custom']

        await settled_eq(my_custom, {'team': 'docs'}, 'profile visible')
        await settled_eq(other_custom, {'team': 'other'}, 'other profile visible')

        # snippet.get_uuid_metadata_builder
        envelope = await pubnub.get_uuid_metadata(include_custom=True).future()
        # snippet.end

        data = envelope.result.data
        a.eq(data['id'], me, 'defaults to the configured user id')
        a.eq((data['name'], data['status'], data['type']), ('Doc profile', 'Active', 'doc'))
        a.eq(data['custom'], {'team': 'docs'})
        a.eq(envelope.result.status, 200)

        # snippet.get_uuid_metadata_named
        metadata = await pubnub.get_uuid_metadata(include_custom=True).future()
        # snippet.end

        a.eq(metadata.result.data, data, 'named arguments: same object')

        plain = checked(await pubnub.get_uuid_metadata().future()).result.data
        a.not_contains(plain, 'custom', 'custom only when included')
        a.not_contains(checked(await pubnub.get_uuid_metadata(include_type=False).future()).result.data, 'type')
        a.not_contains(checked(await pubnub.get_uuid_metadata(include_status=False).future()).result.data, 'status')
        explicit = checked(await pubnub.get_uuid_metadata(uuid=other, include_custom=True).future()).result.data
        a.eq((explicit['id'], explicit['custom']), (other, {'team': 'other'}), 'explicit uuid')
        missing = 'doc_missing'
        e = await expect_error_async(lambda: pubnub.get_uuid_metadata(uuid=missing).future(), '404')
        a.contains(str(e), 'not found')
    finally:
        await cleanup(pubnub, [me, other])


@pytest.mark.timeout(300)
async def test_set_uuid_metadata_builder(aclients):
    """Snippets: set_uuid_metadata_builder, set_uuid_metadata_named."""
    pubnub = aclients.asyncio('open', 'setter')
    first = 'some_uuid'
    second = 'some_uuid_named'
    record(uuids=[first, second])
    try:
        seen = await watch(aclients, first)

        # snippet.set_uuid_metadata_builder
        envelope = await pubnub.set_uuid_metadata(include_custom=True) \
            .uuid("some_uuid") \
            .set_name("Some Name") \
            .set_status("Active") \
            .set_type("User") \
            .email("test@example.com") \
            .profile_url("http://example.com") \
            .external_id("1234567890") \
            .custom({"key1": "val1", "key2": "val2"}) \
            .future()
        # snippet.end

        data = envelope.result.data
        a.eq({k: data[k] for k in UUID_FIELDS}, UUID_FIELDS)
        a.eq((data['id'], data['custom']), (first, {'key1': 'val1', 'key2': 'val2'}))
        a.ok(data['eTag'] and data['updated'], 'eTag and updated are returned')
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['id'], payload['name']), ('uuid', 'set', first, 'Some Name'))
        a.eq(payload['custom'], {'key1': 'val1', 'key2': 'val2'})
        a.eq(payload['eTag'], data['eTag'])
        await settled_eq(lambda: uuid_data(pubnub, first, include_custom=True), data,
                         'read back equals the set response')

        seen = await watch(aclients, second)

        # snippet.set_uuid_metadata_named
        envelope = await pubnub.set_uuid_metadata(uuid="some_uuid_named",
                                                  name="Some Name",
                                                  status="Active", type="User",
                                                  email="test@example.com",
                                                  profile_url="http://example.com",
                                                  external_id="1234567890",
                                                  custom={"key1": "val1", "key2": "val2"},
                                                  include_custom=True) \
            .future()
        # snippet.end

        named = envelope.result.data
        a.eq({k: named[k] for k in UUID_FIELDS}, UUID_FIELDS)
        a.eq((named['id'], named['custom']), (second, {'key1': 'val1', 'key2': 'val2'}))
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['id']), ('uuid', 'set', second))

        # Custom is replaced as a whole, never merged
        replaced = checked(await pubnub.set_uuid_metadata(uuid=first, custom={'only': 'this'},
                                                          include_custom=True).future()).result.data
        a.eq(replaced['custom'], {'only': 'this'})

        async def first_custom():
            return (await uuid_data(pubnub, first, include_custom=True))['custom']

        await settled_eq(first_custom, {'only': 'this'}, 'custom is overwritten')

        # Defaults of the include flags: status and type come back unless they are switched off
        light = pubnub.set_uuid_metadata(uuid=first, name='Some Name', include_status=False, include_type=False)
        light_data = checked(await light.future()).result.data
        a.not_contains(light_data, 'status')
        a.not_contains(light_data, 'type')
        a.not_contains(light_data, 'custom', 'custom only when included')

        # Setting the same data again triggers no event. The first event the watcher sees is the later change.
        fields = dict(name='Some Name', status='Active', type='User', custom={'only': 'this'})
        checked(await pubnub.set_uuid_metadata(uuid=first, **fields).future())
        same = await watch(aclients, first)
        checked(await pubnub.set_uuid_metadata(uuid=first, **fields).future())
        fields['name'] = 'Renamed'
        checked(await pubnub.set_uuid_metadata(uuid=first, **fields).future())
        kind, event, payload = await first_event(same)
        a.eq((event, payload['name']), ('set', 'Renamed'), 'unchanged data raised no event')
    finally:
        await cleanup(pubnub, [first, second])


async def test_remove_uuid_metadata_builder(aclients):
    """Snippets: remove_uuid_metadata_builder, remove_uuid_metadata_named."""
    pubnub = aclients.asyncio('open', 'remover')
    first = 'some_uuid'
    second = 'some_uuid_named'
    record(uuids=[first, second])
    try:
        for uid in (first, second):
            checked(await pubnub.set_uuid_metadata(uuid=uid, name='To remove', custom={'k': 'v'}).future())
        for uid in (first, second):
            async def custom_of():
                return (await uuid_data(pubnub, uid, include_custom=True))['custom']

            await settled_eq(custom_of, {'k': 'v'}, f'{uid} visible')
        seen = await watch(aclients, first)

        # snippet.remove_uuid_metadata_builder
        envelope = await pubnub.remove_uuid_metadata() \
            .uuid("some_uuid").future()
        # snippet.end

        a.eq(envelope.result.status, 200)
        a.eq(envelope.result.data, None, 'nothing is returned')
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['id']), ('uuid', 'delete', first))
        await gone(lambda: pubnub.get_uuid_metadata(uuid=first).future())

        async def second_id():
            return (await uuid_data(pubnub, second))['id']

        await settled_eq(second_id, second, 'other users stay')

        # snippet.remove_uuid_metadata_named
        envelope = await pubnub.remove_uuid_metadata(uuid="some_uuid_named").future()
        # snippet.end

        a.eq(envelope.result.status, 200)
        await gone(lambda: pubnub.get_uuid_metadata(uuid=second).future())

        async def listed_second():
            return (await attempt(lambda: pubnub.get_all_uuid_metadata(
                filter="id == '%s'" % second).future())).result.data

        await settled_eq(listed_second, [], 'the list no longer has the user')
    finally:
        await cleanup(pubnub, [first, second])


async def test_get_all_channel_metadata_builder(aclients):
    """Snippets: get_all_channel_metadata_builder, get_all_channel_metadata_named."""
    pubnub = aclients.asyncio('open', 'lister')
    kind = 'doc_type'
    channels = [('doc_channel_' + x) for x in 'abc']
    record(channels=channels)
    try:
        for rank, channel in enumerate(channels):
            checked(await pubnub.set_channel_metadata(channel=channel, name=kind, type='doc',
                                                      description='Channel %d' % rank,
                                                      custom={'rank': rank}).future())

        async def listed(**kwargs):
            call = pubnub.get_all_channel_metadata(filter="name == '%s'" % kind, **kwargs)
            return (await attempt(lambda: call.future())).result

        async def listed_ids():
            return ids((await listed()).data)

        await settled_eq(listed_ids, sorted(channels), 'seeded channels listed')

        # snippet.get_all_channel_metadata_builder
        from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue
        envelope = await pubnub.get_all_channel_metadata(include_custom=True, include_total_count=True) \
            .limit(10) \
            .filter("name == 'doc_type'") \
            .sort(PNSortKey.asc(PNSortKeyValue.ID), PNSortKey.desc(PNSortKeyValue.UPDATED)) \
            .page(None) \
            .future()
        # snippet.end

        built = envelope.result
        a.eq(ids(built.data), channels, 'ascending by id')
        a.eq(built.total_count, 3)
        a.eq([c['custom'] for c in built.data], [{'rank': 0}, {'rank': 1}, {'rank': 2}])
        a.eq([c['description'] for c in built.data], ['Channel 0', 'Channel 1', 'Channel 2'])

        # snippet.get_all_channel_metadata_named
        from pubnub.models.consumer.objects_v2.sort import PNSortKey, PNSortKeyValue

        metadata = await pubnub.get_all_channel_metadata(limit=10,
                                                         include_custom=True,
                                                         filter="name == 'doc_type'",
                                                         include_total_count=True,
                                                         sort_keys=[PNSortKey.asc(PNSortKeyValue.ID),
                                                                    PNSortKey.desc(PNSortKeyValue.UPDATED)]) \
            .future()
        # snippet.end

        a.eq(ids(metadata.result.data), channels, 'named arguments: same list')
        a.eq(metadata.result.total_count, 3)

        plain = await listed()
        a.not_contains(plain.data[0], 'custom', 'custom only when included')
        a.eq(plain.data[0]['type'], 'doc')
        a.eq(plain.total_count, None)
        a.not_contains((await listed(include_type=False)).data[0], 'type')
        a.not_contains((await listed(include_status=False)).data[0], 'status')
        only = checked(await pubnub.get_all_channel_metadata(
            filter="name == '%s' && id == '%s'" % (kind, channels[2])).future())
        a.eq(ids(only.result.data), [channels[2]], 'filter on name and id')

        ordered = [PNSortKey.asc(PNSortKeyValue.ID)]
        first = await listed(limit=2, sort_keys=ordered)
        a.eq(ids(first.data), channels[:2])
        a.ok(isinstance(first.next, Next), 'next page token')
        second = await listed(limit=2, sort_keys=ordered, page=first.next)
        a.eq(ids(second.data), channels[2:])
        a.ok(isinstance(second.prev, Previous), 'prev page token')
        a.eq(ids((await listed(limit=2, sort_keys=ordered, page=second.prev)).data), channels[:2])
    finally:
        await cleanup(pubnub, channels=channels)


async def test_get_channel_metadata_builder(aclients):
    """Snippets: get_channel_metadata_builder, get_channel_metadata_named."""
    pubnub = aclients.asyncio('open', 'reader')
    channel = 'channel_id'
    record(channels=[channel])
    try:
        checked(await pubnub.set_channel_metadata(channel=channel, name='Doc channel', description='About',
                                                  status='live', type='room', custom={'topic': 'docs'}).future())

        async def topic():
            return (await channel_data(pubnub, channel, include_custom=True))['custom']

        await settled_eq(topic, {'topic': 'docs'}, 'channel visible')

        # snippet.get_channel_metadata_builder
        envelope = await pubnub.get_channel_metadata(include_custom=True) \
            .channel("channel_id") \
            .future()
        # snippet.end

        data = envelope.result.data
        a.eq((data['id'], data['name'], data['description']), (channel, 'Doc channel', 'About'))
        a.eq((data['status'], data['type'], data['custom']), ('live', 'room', {'topic': 'docs'}))
        a.eq(envelope.result.status, 200)

        # snippet.get_channel_metadata_named
        metadata = await pubnub.get_channel_metadata(channel="channel_id", include_custom=True).future()
        # snippet.end

        a.eq(metadata.result.data, data, 'named arguments: same object')
        a.not_contains(checked(await pubnub.get_channel_metadata(channel=channel).future()).result.data, 'custom')
        a.not_contains(checked(await pubnub.get_channel_metadata(
            channel=channel, include_type=False).future()).result.data, 'type')
        a.not_contains(checked(await pubnub.get_channel_metadata(
            channel=channel, include_status=False).future()).result.data, 'status')
        missing = 'doc_missing_channel'
        await expect_error_async(lambda: pubnub.get_channel_metadata(channel=missing).future(), '404')
    finally:
        await cleanup(pubnub, channels=[channel])


@pytest.mark.timeout(300)
async def test_set_channel_metadata_builder(aclients):
    """Snippets: set_channel_metadata_builder, set_channel_metadata_named."""
    pubnub = aclients.asyncio('open', 'setter')
    first = 'channel_id'
    second = 'channel_id_named'
    record(channels=[first, second])
    fields = {'name': 'Channel Name', 'description': 'Description', 'status': 'Archived', 'type': 'Archived'}
    try:
        seen = await watch(aclients, first)

        # snippet.set_channel_metadata_builder
        envelope = await pubnub.set_channel_metadata(include_custom=True) \
            .channel("channel_id") \
            .set_name("Channel Name") \
            .set_status("Archived") \
            .set_type("Archived") \
            .description("Description") \
            .custom({"key1": "val1", "key2": "val2"}) \
            .future()
        # snippet.end

        data = envelope.result.data
        a.eq({k: data[k] for k in fields}, fields)
        a.eq((data['id'], data['custom']), (first, {'key1': 'val1', 'key2': 'val2'}))
        a.ok(data['eTag'] and data['updated'], 'eTag and updated are returned')
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['id'], payload['name']), ('channel', 'set', first, 'Channel Name'))
        a.eq(payload['custom'], {'key1': 'val1', 'key2': 'val2'})
        await settled_eq(lambda: channel_data(pubnub, first, include_custom=True), data,
                         'read back equals the set response')

        seen = await watch(aclients, second)

        # snippet.set_channel_metadata_named
        envelope = await pubnub.set_channel_metadata(channel="channel_id_named",
                                                     name="Channel Name",
                                                     status="Archived",
                                                     type="Archived",
                                                     description="Description",
                                                     custom={"key1": "val1", "key2": "val2"},
                                                     include_custom=True) \
            .future()
        # snippet.end

        named = envelope.result.data
        a.eq({k: named[k] for k in fields}, fields)
        a.eq((named['id'], named['custom']), (second, {'key1': 'val1', 'key2': 'val2'}))
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['id']), ('channel', 'set', second))

        replaced = checked(await pubnub.set_channel_metadata(channel=first, custom={'only': 'this'},
                                                             include_custom=True).future()).result.data
        a.eq(replaced['custom'], {'only': 'this'})

        async def first_custom():
            return (await channel_data(pubnub, first, include_custom=True))['custom']

        await settled_eq(first_custom, {'only': 'this'}, 'custom is overwritten')
        light = checked(await pubnub.set_channel_metadata(channel=first, name='Channel Name', include_status=False,
                                                          include_type=False).future()).result.data
        a.not_contains(light, 'status')
        a.not_contains(light, 'type')
        a.not_contains(light, 'custom', 'custom only when included')

        keep = dict(name='Channel Name', description='Description', status='Archived', type='Archived',
                    custom={'only': 'this'})
        checked(await pubnub.set_channel_metadata(channel=first, **keep).future())
        same = await watch(aclients, first)
        checked(await pubnub.set_channel_metadata(channel=first, **keep).future())
        keep['description'] = 'Changed'
        checked(await pubnub.set_channel_metadata(channel=first, **keep).future())
        kind, event, payload = await first_event(same)
        a.eq((event, payload['description']), ('set', 'Changed'), 'unchanged data raised no event')
    finally:
        await cleanup(pubnub, channels=[first, second])


async def test_remove_channel_metadata_builder(aclients):
    """Snippets: remove_channel_metadata_builder, remove_channel_metadata_named."""
    pubnub = aclients.asyncio('open', 'remover')
    first = 'channel_id'
    second = 'channel_id_named'
    record(channels=[first, second])
    try:
        for channel in (first, second):
            checked(await pubnub.set_channel_metadata(channel=channel, name='To remove').future())
        for channel in (first, second):
            async def name_of():
                return (await channel_data(pubnub, channel))['name']

            await settled_eq(name_of, 'To remove', f'{channel} visible')
        seen = await watch(aclients, first)

        # snippet.remove_channel_metadata_builder
        envelope = await pubnub.remove_channel_metadata() \
            .channel("channel_id") \
            .future()
        # snippet.end

        a.eq(envelope.result.status, 200)
        a.eq(envelope.result.data, None, 'nothing is returned')
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['id']), ('channel', 'delete', first))
        await gone(lambda: pubnub.get_channel_metadata(channel=first).future())

        async def second_id():
            return (await channel_data(pubnub, second))['id']

        await settled_eq(second_id, second, 'other channels stay')

        # snippet.remove_channel_metadata_named
        envelope = await pubnub.remove_channel_metadata(channel="channel_id_named").future()
        # snippet.end

        a.eq(envelope.result.status, 200)
        await gone(lambda: pubnub.get_channel_metadata(channel=second).future())

        async def listed_second():
            return (await attempt(lambda: pubnub.get_all_channel_metadata(
                filter="id == '%s'" % second).future())).result.data

        await settled_eq(listed_second, [], 'the list no longer has the channel')
    finally:
        await cleanup(pubnub, channels=[first, second])


async def test_get_memberships_builder(aclients):
    """Snippets: get_memberships_builder, get_memberships_named."""
    pubnub = aclients.asyncio('open', 'reader')
    uid = 'some_uuid'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([uid], [plain, with_custom])
    try:
        await fresh(pubnub, [uid], [plain, with_custom])
        await seed_channels(pubnub, plain, with_custom)
        await seed_memberships(pubnub, uid, plain, with_custom)
        await memberships_visible(pubnub, uid, plain, with_custom)

        # snippet.get_memberships_builder
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        envelope = await pubnub.get_memberships() \
            .include(MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .uuid("some_uuid").future()
        # snippet.end

        check_memberships(envelope.result.data, plain, with_custom)
        a.eq(envelope.result.status, 200)

        # snippet.get_memberships_named
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes

        envelope = await pubnub.get_memberships(uuid="some_uuid",
                                                include=MembershipIncludes(custom=True, channel=True,
                                                                           channel_custom=True)) \
            .future()
        # snippet.end

        check_memberships(envelope.result.data, plain, with_custom)

        # Details appear only when they are included
        bare = await memberships_of(pubnub, uid)
        a.not_contains(bare[0], 'custom', 'custom only when included')
        a.eq(bare[0]['channel'], {'id': bare[0]['channel']['id']}, 'channel is only an id by default')
        only_custom = await memberships_of(pubnub, uid, include=MembershipIncludes(custom=True))
        a.contains(only_custom[0], 'custom')
        a.eq(by_channel(only_custom)[with_custom]['custom'], CUSTOM_2)
        a.not_contains(bare[0], 'type')
        a.not_contains(bare[0], 'status')
        typed = PNChannelMembership(plain, status='active', type='doc')
        checked(await pubnub.set_memberships(uuid=uid, channel_memberships=[typed]).future())

        async def typed_of():
            found = await memberships_of(pubnub, uid, include=MembershipIncludes(type=True, status=True))
            return [(m['type'], m['status']) for m in found if m['channel']['id'] == plain]

        await settled_eq(typed_of, [('doc', 'active')], 'type and status of the membership')

        filtered = await memberships_of(pubnub, uid, filter="channel.name LIKE 'some name with*'")
        a.eq(channel_ids(filtered), [with_custom], 'filter on the channel name')
        counted = checked(await pubnub.get_memberships(uuid=uid).include_total_count(True).future()).result
        a.eq(counted.total_count, 2, 'total count')

        # Paging with next and prev, sorted by the update time (the only sort key the service accepts here)
        newest = [PNSortKey.desc(PNSortKeyValue.UPDATED)]
        first = checked(await pubnub.get_memberships(uuid=uid, limit=1, sort_keys=newest).future()).result
        a.eq(len(first.data), 1)
        a.ok(isinstance(first.next, Next), 'next page token')
        second = checked(await pubnub.get_memberships(uuid=uid, limit=1, sort_keys=newest,
                                                      page=first.next).future()).result
        a.eq(sorted(channel_ids(first.data + second.data)), sorted([plain, with_custom]), 'two pages cover both')
        a.ok(isinstance(second.prev, Previous), 'prev page token')
        back = checked(await pubnub.get_memberships(uuid=uid, limit=1, sort_keys=newest,
                                                    page=second.prev).future()).result
        a.eq(channel_ids(back.data), channel_ids(first.data), 'prev returns the first page')
    finally:
        await cleanup(pubnub, [uid], [plain, with_custom])


@pytest.mark.timeout(300)
async def test_set_memberships_builder(aclients):
    """Snippets: set_memberships_builder, set_memberships_named."""
    pubnub = aclients.asyncio('open', 'setter')
    first = 'some_uuid'
    second = 'some_uuid_named'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([first, second], [plain, with_custom])
    try:
        await fresh(pubnub, [first, second], [plain, with_custom])
        seen = await watch(aclients, first)

        # snippet.set_memberships_builder
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        await pubnub.set_channel_metadata() \
            .channel(some_channel) \
            .set_name("some name") \
            .future()

        custom_1 = {
            "key3": "val1",
            "key4": "val2",
        }

        await pubnub.set_channel_metadata() \
            .channel(some_channel_with_custom) \
            .set_name("some name with custom") \
            .custom(custom_1) \
            .future()

        custom_2 = {
            "key5": "val1",
            "key6": "val2",
        }

        channel_memberships_to_set = [
            PNChannelMembership.channel(some_channel),
            PNChannelMembership.channel_with_custom(some_channel_with_custom, custom_2),
        ]

        envelope = await pubnub.set_memberships() \
            .uuid("some_uuid") \
            .channel_memberships(channel_memberships_to_set) \
            .include(MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .future()
        # snippet.end

        check_memberships(envelope.result.data, plain, with_custom)
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['uuid']['id']), ('membership', 'set', first))
        a.contains([plain, with_custom], payload['channel']['id'])

        seen = await watch(aclients, second)

        # snippet.set_memberships_named
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership

        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        await pubnub.set_channel_metadata(channel=some_channel, name="some name").future()

        custom_1 = {
            "key3": "val1",
            "key4": "val2",
        }

        await pubnub.set_channel_metadata(channel=some_channel_with_custom,
                                          name="some name with custom",
                                          custom=custom_1) \
            .future()

        custom_2 = {
            "key5": "val1",
            "key6": "val2",
        }

        channel_memberships_to_set = [
            PNChannelMembership.channel(some_channel),
            PNChannelMembership.channel_with_custom(some_channel_with_custom, custom_2),
        ]

        envelope = await pubnub.set_memberships(uuid="some_uuid_named",
                                                channel_memberships=channel_memberships_to_set,
                                                include=MembershipIncludes(custom=True, channel=True,
                                                                           channel_custom=True)) \
            .future()
        # snippet.end

        check_memberships(envelope.result.data, plain, with_custom)
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['uuid']['id']), ('membership', 'set', second))

        # The channel side sees the same memberships
        await settled_eq(lambda: sorted_of(users_of(pubnub, plain)), sorted([first, second]),
                         'both users are members')

        # Set adds to the stored memberships, it does not replace them
        extra = 'somechannel_extra'
        record(channels=[extra])
        try:
            checked(await pubnub.set_channel_metadata(channel=extra, name='extra').future())
            added = checked(await pubnub.set_memberships(
                uuid=first, channel_memberships=[PNChannelMembership.channel(extra)]).future())
            a.eq(sorted(channel_ids(added.result.data)), sorted([plain, with_custom, extra]), 'set keeps the others')
        finally:
            await cleanup(pubnub, [first], [extra])
    finally:
        await cleanup(pubnub, [first, second], [plain, with_custom])


@pytest.mark.timeout(300)
async def test_remove_memberships_builder(aclients):
    """Snippets: remove_memberships_builder, remove_memberships_named."""
    pubnub = aclients.asyncio('open', 'remover')
    first = 'some_uuid'
    second = 'some_uuid_named'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([first, second], [plain, with_custom])
    try:
        await fresh(pubnub, [first, second], [plain, with_custom])
        await seed_channels(pubnub, plain, with_custom)
        for uid in (first, second):
            await seed_memberships(pubnub, uid, plain, with_custom)
        for uid in (first, second):
            await settled_eq(lambda: sorted_of(channels_of(pubnub, uid)), sorted([plain, with_custom]),
                             f'memberships of {uid} seeded')
        seen = await watch(aclients, first)

        # snippet.remove_memberships_builder
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
        some_channel = "somechannel"

        envelope = await pubnub.remove_memberships() \
            .uuid("some_uuid") \
            .channel_memberships([PNChannelMembership.channel(some_channel)]) \
            .include(MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .future()
        # snippet.end

        left = envelope.result.data
        a.eq(channel_ids(left), [with_custom], 'the response lists the remaining memberships')
        a.eq(left[0]['custom'], CUSTOM_2)
        a.eq(left[0]['channel']['custom'], CUSTOM_1)
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['uuid']['id'], payload['channel']['id']), ('membership', 'delete', first, plain))
        await settled_eq(lambda: channels_of(pubnub, first), [with_custom], 'membership removed')

        async def second_count():
            return len(await memberships_of(pubnub, second))

        await settled_eq(second_count, 2, 'other users keep theirs')

        # snippet.remove_memberships_named
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership

        envelope = await pubnub.remove_memberships(uuid="some_uuid_named",
                                                   channel_memberships=[PNChannelMembership.channel(some_channel)],
                                                   include=MembershipIncludes(custom=True, channel=True,
                                                                              channel_custom=True)) \
            .future()
        # snippet.end

        a.eq(channel_ids(envelope.result.data), [with_custom])
        a.eq(envelope.result.data[0]['channel']['custom'], CUSTOM_1)
        await settled_eq(lambda: channels_of(pubnub, second), [with_custom], 'second membership removed')

        async def plain_id():
            return (await channel_data(pubnub, plain))['id']

        await settled_eq(plain_id, plain, 'the channel stays')
    finally:
        await cleanup(pubnub, [first, second], [plain, with_custom])


@pytest.mark.timeout(300)
async def test_manage_memberships_builder(aclients):
    """Snippets: manage_memberships_builder, manage_memberships_named."""
    pubnub = aclients.asyncio('open', 'manager')
    first = 'some_uuid'
    second = 'some_uuid_named'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([first, second], [plain, with_custom])
    try:
        await fresh(pubnub, [first, second], [plain, with_custom])
        await seed_channels(pubnub, plain, with_custom)
        for uid in (first, second):
            await seed_one_membership(pubnub, uid, with_custom)
        for uid in (first, second):
            await settled_eq(lambda: channels_of(pubnub, uid), [with_custom], f'seed of {uid} visible')
        seen = await watch(aclients, first)

        # snippet.manage_memberships_builder
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
        some_channel = "somechannel"
        some_channel_with_custom = "somechannel_with_custom"

        envelope = await pubnub.manage_memberships() \
            .uuid("some_uuid") \
            .set([PNChannelMembership.channel(some_channel)]) \
            .remove([PNChannelMembership.channel(some_channel_with_custom)]) \
            .include(MembershipIncludes(custom=True, channel=True, channel_custom=True)) \
            .future()
        # snippet.end

        a.eq(channel_ids(envelope.result.data), [plain], 'the response lists the remaining memberships')
        a.eq(envelope.result.data[0]['channel']['name'], 'some name')
        kind, event, payload = await first_event(seen)
        a.eq(kind, 'membership')
        a.contains([('set', plain), ('delete', with_custom)], (event, payload['channel']['id']))
        await settled_eq(lambda: channels_of(pubnub, first), [plain], 'memberships changed')

        # snippet.manage_memberships_named
        from pubnub.models.consumer.objects_v2.common import MembershipIncludes
        from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership

        envelope = await pubnub.manage_memberships(uuid="some_uuid_named",
                                                   channel_memberships_to_set=[
                                                       PNChannelMembership.channel(some_channel)],
                                                   channel_memberships_to_remove=[
                                                       PNChannelMembership.channel(some_channel_with_custom)],
                                                   include=MembershipIncludes(custom=True, channel=True,
                                                                              channel_custom=True)) \
            .future()
        # snippet.end

        a.eq(channel_ids(envelope.result.data), [plain])
        await settled_eq(lambda: channels_of(pubnub, second), [plain], 'second user changed')
    finally:
        await cleanup(pubnub, [first, second], [plain, with_custom])


async def test_get_channel_members_builder(aclients):
    """Snippets: get_channel_members_builder, get_channel_members_named."""
    pubnub = aclients.asyncio('open', 'reader')
    channel = 'channel_id'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [channel])
    try:
        await fresh(pubnub, [plain, with_custom], [channel])
        await seed_users(pubnub, plain, with_custom)
        checked(await pubnub.set_channel_metadata(channel=channel, name='Doc channel').future())
        await seed_members(pubnub, channel, plain, with_custom)
        await members_visible(pubnub, channel, plain, with_custom)

        # snippet.get_channel_members_builder
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        envelope = await pubnub.get_channel_members() \
            .channel("channel_id") \
            .include(MemberIncludes(custom=True, user=True, user_custom=True)) \
            .future()
        # snippet.end

        check_members(envelope.result.data, plain, with_custom)
        a.eq(envelope.result.status, 200)

        # snippet.get_channel_members_named
        from pubnub.models.consumer.objects_v2.common import MemberIncludes

        envelope = await pubnub.get_channel_members(channel="channel_id",
                                                    include=MemberIncludes(custom=True, user=True,
                                                                           user_custom=True)) \
            .future()
        # snippet.end

        check_members(envelope.result.data, plain, with_custom)

        bare = await members_of(pubnub, channel)
        a.not_contains(bare[0], 'custom', 'custom only when included')
        a.eq(bare[0]['uuid'], {'id': bare[0]['uuid']['id']}, 'the user is only an id by default')
        only_custom = await members_of(pubnub, channel, include=MemberIncludes(custom=True))
        a.eq(by_member(only_custom)[with_custom]['custom'], CUSTOM_2)

        # Member filters address the user as uuid.name, uuid.description is not a filter property
        filtered = await members_of(pubnub, channel, filter="uuid.name LIKE 'some name with*'")
        a.eq(member_ids(filtered), [with_custom], 'filter on the user name')
        counted = checked(await pubnub.get_channel_members(channel=channel).include_total_count(True).future()).result
        a.eq(counted.total_count, 2, 'total count')

        newest = [PNSortKey.desc(PNSortKeyValue.UPDATED)]
        first = checked(await pubnub.get_channel_members(channel=channel, limit=1, sort_keys=newest).future()).result
        a.eq(len(first.data), 1)
        a.ok(isinstance(first.next, Next), 'next page token')
        second = checked(await pubnub.get_channel_members(channel=channel, limit=1, sort_keys=newest,
                                                          page=first.next).future()).result
        a.eq(sorted(member_ids(first.data + second.data)), sorted([plain, with_custom]), 'two pages cover both')
        a.ok(isinstance(second.prev, Previous), 'prev page token')
        back = checked(await pubnub.get_channel_members(channel=channel, limit=1, sort_keys=newest,
                                                        page=second.prev).future()).result
        a.eq(member_ids(back.data), member_ids(first.data), 'prev returns the first page')
    finally:
        await cleanup(pubnub, [plain, with_custom], [channel])


@pytest.mark.timeout(300)
async def test_set_channel_members_builder(aclients):
    """Snippets: set_channel_members_builder, set_channel_members_named."""
    pubnub = aclients.asyncio('open', 'setter')
    first = 'channel_id'
    second = 'channel_id_named'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [first, second])
    try:
        await fresh(pubnub, [plain, with_custom, 'some_uuid_extra'], [first, second])
        seen = await watch(aclients, first)

        # snippet.set_channel_members_builder
        from pubnub.models.consumer.objects_v2.channel_members import PNUserMember
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        await pubnub.set_uuid_metadata() \
            .uuid("some_uuid") \
            .set_name("some name") \
            .future()

        custom_1 = {
            "key3": "val1",
            "key4": "val2"
        }

        await pubnub.set_uuid_metadata() \
            .uuid("some_uuid_with_custom") \
            .set_name("some name with custom") \
            .custom(custom_1) \
            .future()

        custom_2 = {
            "key5": "val1",
            "key6": "val2"
        }

        uuids_to_set = [
            PNUserMember(user_id="some_uuid"),
            PNUserMember(user_id="some_uuid_with_custom", custom=custom_2)
        ]

        envelope = await pubnub.set_channel_members() \
            .channel("channel_id") \
            .uuids(uuids_to_set) \
            .include(MemberIncludes(custom=True, user=True, user_custom=True)) \
            .future()
        # snippet.end

        check_members(envelope.result.data, plain, with_custom)
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['channel']['id']), ('membership', 'set', first))
        a.contains([plain, with_custom], payload['uuid']['id'])

        seen = await watch(aclients, second)

        # snippet.set_channel_members_named
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        from pubnub.models.consumer.objects_v2.channel_members import PNUserMember

        await pubnub.set_uuid_metadata(uuid="some_uuid", name="some name").future()

        custom_1 = {
            "key3": "val1",
            "key4": "val2"
        }

        await pubnub.set_uuid_metadata(uuid="some_uuid_with_custom",
                                       name="some name with custom",
                                       custom=custom_1) \
            .future()

        custom_2 = {
            "key5": "val1",
            "key6": "val2"
        }

        uuids_to_set = [
            PNUserMember(user_id="some_uuid"),
            PNUserMember(user_id="some_uuid_with_custom", custom=custom_2)
        ]

        envelope = await pubnub.set_channel_members(channel="channel_id_named",
                                                    uuids=uuids_to_set,
                                                    include=MemberIncludes(custom=True, user=True,
                                                                           user_custom=True)) \
            .future()
        # snippet.end

        check_members(envelope.result.data, plain, with_custom)
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['channel']['id']), ('membership', 'set', second))

        await settled_eq(lambda: sorted_of(channels_of(pubnub, plain)), sorted([first, second]),
                         'the user side sees both channels')

        # Set adds to the stored members, it does not replace them
        extra = 'some_uuid_extra'
        record(uuids=[extra])
        try:
            checked(await pubnub.set_uuid_metadata(uuid=extra, name='extra').future())
            added = checked(await pubnub.set_channel_members(channel=first, uuids=[PNUserMember(user_id=extra)]).future())
            a.eq(sorted(member_ids(added.result.data)), sorted([plain, with_custom, extra]), 'set keeps the others')
        finally:
            await cleanup(pubnub, [extra], [])
    finally:
        await cleanup(pubnub, [plain, with_custom], [first, second])


@pytest.mark.timeout(300)
async def test_remove_channel_members_builder(aclients):
    """Snippets: remove_channel_members_builder, remove_channel_members_named."""
    pubnub = aclients.asyncio('open', 'remover')
    first = 'channel_id'
    second = 'channel_id_named'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [first, second])
    try:
        await fresh(pubnub, [plain, with_custom, 'some_uuid_extra'], [first, second])
        await seed_users(pubnub, plain, with_custom)
        for channel in (first, second):
            checked(await pubnub.set_channel_metadata(channel=channel, name='Doc channel').future())
            await seed_members(pubnub, channel, plain, with_custom)
        for channel in (first, second):
            await settled_eq(lambda: sorted_of(users_of(pubnub, channel)), sorted([plain, with_custom]),
                             f'members of {channel} seeded')
        seen = await watch(aclients, first)

        # snippet.remove_channel_members_builder
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        from pubnub.models.consumer.objects_v2.channel_members import PNUserMember
        envelope = await pubnub.remove_channel_members() \
            .channel("channel_id") \
            .uuids([PNUserMember(user_id="some_uuid")]) \
            .include(MemberIncludes(custom=True, user=True, user_custom=True)) \
            .future()
        # snippet.end

        left = envelope.result.data
        a.eq(member_ids(left), [with_custom], 'the response lists the remaining members')
        a.eq(left[0]['custom'], CUSTOM_2)
        a.eq(left[0]['uuid']['custom'], CUSTOM_1)
        kind, event, payload = await first_event(seen)
        a.eq((kind, event, payload['channel']['id'], payload['uuid']['id']), ('membership', 'delete', first, plain))
        await settled_eq(lambda: users_of(pubnub, first), [with_custom], 'member removed')

        async def second_count():
            return len(await members_of(pubnub, second))

        await settled_eq(second_count, 2, 'other channels keep theirs')

        # snippet.remove_channel_members_named
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        from pubnub.models.consumer.objects_v2.channel_members import PNUserMember

        envelope = await pubnub.remove_channel_members(channel="channel_id_named",
                                                       uuids=[PNUserMember(user_id="some_uuid")],
                                                       include=MemberIncludes(custom=True, user=True,
                                                                              user_custom=True)) \
            .future()
        # snippet.end

        a.eq(member_ids(envelope.result.data), [with_custom])
        a.eq(envelope.result.data[0]['uuid']['custom'], CUSTOM_1)
        await settled_eq(lambda: users_of(pubnub, second), [with_custom], 'second member removed')

        async def plain_id():
            return (await uuid_data(pubnub, plain))['id']

        await settled_eq(plain_id, plain, 'the user stays')
    finally:
        await cleanup(pubnub, [plain, with_custom], [first, second])


@pytest.mark.timeout(300)
async def test_manage_channel_members_builder(aclients):
    """Snippets: manage_channel_members_builder, manage_channel_members_named."""
    pubnub = aclients.asyncio('open', 'manager')
    first = 'channel_id'
    second = 'channel_id_named'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [first, second])
    try:
        await fresh(pubnub, [plain, with_custom, 'some_uuid_extra'], [first, second])
        await seed_users(pubnub, plain, with_custom)
        for channel in (first, second):
            checked(await pubnub.set_channel_metadata(channel=channel, name='Doc channel').future())
            await seed_one_member(pubnub, channel, with_custom)
        for channel in (first, second):
            await settled_eq(lambda: users_of(pubnub, channel), [with_custom], f'seed of {channel} visible')
        seen = await watch(aclients, first)

        # snippet.manage_channel_members_builder
        from pubnub.models.consumer.objects_v2.channel_members import PNUserMember
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        envelope = await pubnub.manage_channel_members() \
            .channel("channel_id") \
            .set([PNUserMember(user_id="some_uuid")]) \
            .remove([PNUserMember(user_id="some_uuid_with_custom")]) \
            .include(MemberIncludes(custom=True, user=True, user_custom=True)) \
            .future()
        # snippet.end

        a.eq(member_ids(envelope.result.data), [plain], 'the response lists the remaining members')
        a.eq(envelope.result.data[0]['uuid']['name'], 'some name')
        kind, event, payload = await first_event(seen)
        a.eq(kind, 'membership')
        a.contains([('set', plain), ('delete', with_custom)], (event, payload['uuid']['id']))
        await settled_eq(lambda: users_of(pubnub, first), [plain], 'members changed')

        # snippet.manage_channel_members_named
        from pubnub.models.consumer.objects_v2.common import MemberIncludes
        from pubnub.models.consumer.objects_v2.channel_members import PNUserMember

        envelope = await pubnub.manage_channel_members(channel="channel_id_named",
                                                       uuids_to_set=[PNUserMember(user_id="some_uuid")],
                                                       uuids_to_remove=[PNUserMember(user_id="some_uuid_with_custom")],
                                                       include=MemberIncludes(custom=True, user=True,
                                                                              user_custom=True)) \
            .future()
        # snippet.end

        a.eq(member_ids(envelope.result.data), [plain])
        await settled_eq(lambda: users_of(pubnub, second), [plain], 'second channel changed')
    finally:
        await cleanup(pubnub, [plain, with_custom], [first, second])


async def test_pnchannelmembership_class(aclients):
    """Snippet: pnchannelmembership_class."""
    pubnub = aclients.asyncio('open', 'classes')
    uid = 'some_uuid'
    plain = 'somechannel'
    with_custom = 'somechannel_with_custom'
    record([uid], [plain, with_custom])
    try:
        await fresh(pubnub, [uid], [plain, with_custom, 'channel_id'])
        await seed_channels(pubnub, plain, with_custom)

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
        checked(await pubnub.set_memberships(uuid=uid, channel_memberships=[membership,
                                                                            membership_with_custom]).future())

        async def customs():
            found = await memberships_of(pubnub, uid, include=MembershipIncludes(custom=True))
            return {m['channel']['id']: m['custom'] for m in found}

        await settled_eq(customs, {plain: None, with_custom: CUSTOM_2}, 'memberships set from the helper objects')
    finally:
        await cleanup(pubnub, [uid], [plain, with_custom])


async def test_pnuuid_class(aclients):
    """Snippet: pnuuid_class."""
    pubnub = aclients.asyncio('open', 'classes')
    channel = 'channel_id'
    plain = 'some_uuid'
    with_custom = 'some_uuid_with_custom'
    record([plain, with_custom], [channel])
    try:
        await fresh(pubnub, [plain, with_custom, 'some_uuid_extra'], [channel])
        await seed_users(pubnub, plain, with_custom)
        checked(await pubnub.set_channel_metadata(channel=channel, name='Doc channel').future())

        # snippet.pnuuid_class
        from pubnub.models.consumer.objects_v2.channel_members import PNUserMember
        member = PNUserMember(user_id="some_uuid")
        member_with_custom = PNUserMember(user_id="some_uuid_with_custom", custom={"key5": "val1", "key6": "val2"})
        # snippet.end

        a.eq(type(member).__name__, 'PNUserMember')
        a.eq(type(member_with_custom).__name__, 'PNUserMember')
        a.eq(member.to_payload_dict(), {'uuid': {'id': plain}})
        a.eq(member_with_custom.to_payload_dict(), {'uuid': {'id': with_custom}, 'custom': CUSTOM_2})
        checked(await pubnub.set_channel_members(channel=channel, uuids=[member, member_with_custom]).future())

        async def customs():
            found = await members_of(pubnub, channel, include=MemberIncludes(custom=True))
            return {m['uuid']['id']: m['custom'] for m in found}

        await settled_eq(customs, {plain: None, with_custom: CUSTOM_2}, 'members set from the helper objects')
    finally:
        await cleanup(pubnub, [plain, with_custom], [channel])
