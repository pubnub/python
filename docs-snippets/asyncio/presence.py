"""Docs page: presence (asyncio). Same steps as sync/presence.py with await.

Presence needs channel tracking on the keyset. Joins of a second client are asserted, never the client's own join,
and here_now is polled with aeventually because the service reports it with a delay and caches it for 3 seconds.
"""
from harness import assertions as a
from harness import names
from harness import world
from harness.listeners import alisten
from harness.step import step
from harness.wait import aeventually

REGISTERED_NAMES = ['cg2', 'cg3', 'gr1', 'gr2', 'gr3', 'such_uuid', 'some-other-uuid']


class Printed:
    """Everything the docs code printed so far."""

    def __init__(self, capsys):
        self._capsys = capsys
        self._parts = []

    def text(self):
        self._parts.append(self._capsys.readouterr().out)
        return ''.join(self._parts)


def occupants_of(here_now, channel):
    """uuids of one channel in a PNHereNowResult, sorted. The result holds a list of PNHereNowChannelData."""
    found = [c for c in here_now.result.channels if c.channel_name == channel]
    return sorted(o.uuid for o in found[0].occupants) if found and found[0].occupants is not None else None


def occupancy_of(here_now, channel):
    found = [c for c in here_now.result.channels if c.channel_name == channel]
    return found[0].occupancy if found else None


@step('here_now_builder', role='open')
async def test_here_now(aclients, capsys):
    pubnub = aclients.asyncio('open', 'reader')
    first, second = names.with_suffix('my_channel'), names.with_suffix('my_channel_2')
    printed = Printed(capsys)
    one = aclients.asyncio('open', 'user_one')
    two = aclients.asyncio('open', 'user_two')
    await alisten(one, first, second)
    await alisten(two, first)
    expected = {first: sorted([one.uuid, two.uuid]), second: [one.uuid]}

    async def builder():
        # snippet.here_now_builder
        envelope = await pubnub.here_now() \
            .channels(["my_channel", "my_channel_2"]) \
            .include_uuids(True) \
            .future()

        if envelope.status.is_error():
            print("Error retrieving here_now data")
            return

        for channel_data in envelope.result.channels:
            print("---")
            print(f"Channel: {channel_data.channel_name}")
            print(f"Occupancy: {channel_data.occupancy}")
            for occupant in channel_data.occupants:
                print(f"UUID: {occupant.uuid}, State: {occupant.state}")
        # snippet.end
        return envelope

    async def check():
        result = await builder()
        a.ok(result is not None, 'here_now returned an error')
        a.eq({c: occupants_of(result, c) for c in expected}, expected, 'occupants per channel')
        a.eq((result.result.total_channels, result.result.total_occupancy), (2, 3))
    await aeventually(check, what='here_now lists both clients')
    text = printed.text()
    a.contains(text, f'Channel: {first}\nOccupancy: 2\n')
    a.contains(text, f'UUID: {one.uuid}, State: None')
    a.contains(text, f'Channel: {second}\nOccupancy: 1\n')


@step('here_now_state', role='open')
async def test_here_now_state(aclients):
    pubnub = aclients.asyncio('open', 'reader')
    name = names.with_suffix('my_channel')
    one = aclients.asyncio('open', 'user_one')
    await alisten(one, name)
    await one.set_state().channels(name).state({'abcd': {'age': 15}}).future()

    async def read():
        # snippet.here_now_state
        envelope = await pubnub.here_now() \
            .channels("my_channel") \
            .include_uuids(True) \
            .include_state(True) \
            .future()
        # snippet.end
        return envelope

    async def check():
        envelope = await read()
        found = [(o.uuid, o.state) for c in envelope.result.channels for o in c.occupants]
        a.eq(found, [(one.uuid, {'abcd': {'age': 15}})], 'occupants with state')
        a.eq((envelope.result.total_channels, envelope.result.total_occupancy), (1, 1))
    await aeventually(check, what='here_now returns the state')


@step('here_now_occupancy', role='open')
async def test_here_now_occupancy(aclients):
    pubnub = aclients.asyncio('open', 'reader')
    name = names.with_suffix('my_channel')
    for who in ('user_one', 'user_two', 'user_three'):
        await alisten(aclients.asyncio('open', who), name)

    async def read():
        # snippet.here_now_occupancy
        envelope = await pubnub.here_now() \
            .channels("my_channel") \
            .include_uuids(False) \
            .include_state(False) \
            .future()
        # snippet.end
        return envelope

    async def check():
        envelope = await read()
        a.eq([(c.channel_name, c.occupancy, c.occupants) for c in envelope.result.channels], [(name, 3, [])])
        a.eq((envelope.result.total_channels, envelope.result.total_occupancy), (1, 3))
    await aeventually(check, what='here_now counts three occupants')


@step('here_now_groups', role='open')
async def test_here_now_groups(aclients):
    pubnub = aclients.asyncio('open', 'reader')
    groups = [names.with_suffix(n) for n in ('cg1', 'cg2', 'cg3')]
    members = [names.with_suffix(f'grouped_{i}') for i in (1, 2, 3)]
    for group, member in zip(groups, members):
        await pubnub.add_channel_to_channel_group().channels([member]).channel_group(group).future()
        world.record('channel_group', group)
    one = aclients.asyncio('open', 'user_one')
    await alisten(one, *members)

    async def read():
        # snippet.here_now_groups
        envelope = await pubnub.here_now() \
            .channel_groups(['cg1', 'cg2', 'cg3']) \
            .include_uuids(True) \
            .include_state(True) \
            .future()
        # snippet.end
        return envelope

    async def check():
        envelope = await read()
        a.eq(sorted((c.channel_name, c.occupancy, [o.uuid for o in c.occupants]) for c in envelope.result.channels),
             sorted((m, 1, [one.uuid]) for m in members), 'every channel of the groups with its occupant')
        a.eq((envelope.result.total_channels, envelope.result.total_occupancy), (3, 3))
    await aeventually(check, what='here_now by channel group')


@step('where_now_self', 'where_now_other', role='open')
async def test_where_now(aclients):
    pubnub = aclients.asyncio('open', 'reader')
    first, second = names.with_suffix('my_channel'), names.with_suffix('my_channel_2')
    await alisten(pubnub, first, second)
    other = aclients.asyncio('open', 'some-other-uuid')
    await alisten(other, first)

    async def own():
        # snippet.where_now_self
        envelope = await pubnub.where_now() \
            .future()
        # snippet.end
        return envelope

    async def elsewhere():
        # snippet.where_now_other
        envelope = await pubnub.where_now() \
            .uuid('some-other-uuid') \
            .future()
        # snippet.end
        return envelope

    async def check_own():
        a.eq(sorted((await own()).result.channels), sorted([first, second]), 'own channels')

    async def check_other():
        a.eq((await elsewhere()).result.channels, [first], 'channels of the other user ID')
    await aeventually(check_own)
    await aeventually(check_other)


@step('set_state_builder', 'get_state_builder', role='open')
async def test_state(aclients):
    pubnub = aclients.asyncio('open', 'such_uuid')
    reader = aclients.asyncio('open', 'reader')
    channels = [names.with_suffix(n) for n in ('ch1', 'ch2', 'ch3')]
    await alisten(pubnub, *channels)

    # snippet.set_state_builder
    my_state = {
        'age': 20
    }
    envelope = await pubnub.set_state() \
        .channels(['ch1', 'ch2', 'ch3']) \
        .state(my_state) \
        .future()
    # snippet.end
    a.eq(envelope.result.state, {'age': 20}, 'state returned by set_state')

    # snippet.get_state_builder
    envelope = await pubnub.get_state() \
        .channels(['ch1', 'ch2', 'ch3']) \
        .uuid('such_uuid') \
        .future()
    # snippet.end
    a.eq(envelope.result.channels, {c: {'age': 20} for c in channels}, 'state per channel')
    fetched = await reader.get_state().channels(channels[0]).uuid(pubnub.uuid).future()
    a.eq(fetched.result.channels, {channels[0]: {'age': 20}}, 'another client reads the state')


@step('set_state_groups_builder', role='open')
async def test_state_for_groups(aclients):
    pubnub = aclients.asyncio('open', 'such_uuid')
    groups = [names.with_suffix(n) for n in ('gr1', 'gr2', 'gr3')]
    members = [names.with_suffix(f'grouped_{i}') for i in (1, 2, 3)]
    own = names.with_suffix('ch1')
    for group, member in zip(groups, members):
        await pubnub.add_channel_to_channel_group().channels([member]).channel_group(group).future()
        world.record('channel_group', group)
    await alisten(pubnub, own, *members, groups=groups)
    # The SDK refuses a set_state() that names channel groups and no channel (PubNubException "State setter for
    # channel groups is not supported yet" in sync, an error status in asyncio), so the sample below adds a
    # channel next to the groups.
    refusal = await pubnub.set_state().channel_groups(groups).state({'age': 20}).future()
    a.ok(refusal.status.is_error(), 'set_state with only channel groups is refused')

    # snippet.set_state_groups_builder
    my_state = {
        'age': 20
    }
    envelope = await pubnub.set_state() \
        .channels(['ch1']) \
        .channel_groups(['gr1', 'gr2', 'gr3']) \
        .state(my_state) \
        .future()
    # snippet.end
    a.eq(envelope.result.state, {'age': 20}, 'state returned by set_state for groups')
    own_state = await pubnub.get_state().channels(own).future()
    a.eq(own_state.result.channels, {own: {'age': 20}})
    group_state = await pubnub.get_state().channel_groups(groups).future()
    a.eq(group_state.result.channels, {m: {'age': 20} for m in members}, 'state read back through the channel groups')
