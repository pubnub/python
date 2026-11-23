"""Docs page: presence (asyncio). Same steps as sync/presence.py with await.

Presence needs channel tracking on the keyset. Joins of a second client are asserted, never the client's own join,
and here_now is polled with aeventually because the service reports it with a delay and caches it for 3 seconds.
"""
from support import assertions as a
from support import cleanup as live_cleanup
from support.listen import alisten
from support.wait import aeventually
from shared.presence import Printed, consistent, occupancy_of, own_occupants, present


async def test_here_now_builder(aclients, capsys):
    """Snippet: here_now_builder."""
    pubnub = aclients.asyncio('open', 'reader')
    first, second = 'my_channel', 'my_channel_2'
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
        a.eq({c: own_occupants(result, c, expected[c]) for c in expected}, expected, 'own occupants per channel')
        a.eq(result.result.total_channels, 2)
        consistent(result)
        return result
    last = await aeventually(check, what='here_now lists both clients')
    text = printed.text()
    a.contains(text, f'Channel: {first}\nOccupancy: {occupancy_of(last, first)}\n')
    a.contains(text, f'UUID: {one.uuid}, State: None')
    a.contains(text, f'Channel: {second}\nOccupancy: {occupancy_of(last, second)}\n')


async def test_here_now_state(aclients):
    """Snippet: here_now_state."""
    pubnub = aclients.asyncio('open', 'reader')
    name = 'my_channel'
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
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        return envelope

    async def check():
        envelope = await read()
        found = [(o.uuid, o.state) for c in envelope.result.channels for o in c.occupants]
        a.contains(found, (one.uuid, {'abcd': {'age': 15}}), 'own occupant with state')
        a.eq(envelope.result.total_channels, 1)
        consistent(envelope)
    await aeventually(check, what='here_now returns the state')


async def test_here_now_occupancy(aclients):
    """Snippet: here_now_occupancy."""
    pubnub = aclients.asyncio('open', 'reader')
    name = 'my_channel'
    mine = ['user_one', 'user_two', 'user_three']
    for who in mine:
        await alisten(aclients.asyncio('open', who), name)

    async def read():
        # snippet.here_now_occupancy
        envelope = await pubnub.here_now() \
            .channels("my_channel") \
            .include_uuids(False) \
            .include_state(False) \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        return envelope

    async def check():
        envelope = await read()
        a.eq([(c.channel_name, c.occupants) for c in envelope.result.channels], [(name, [])], 'no user IDs')
        a.ok(occupancy_of(envelope, name) >= len(mine), 'the count includes the three own occupants')
        a.eq(envelope.result.total_occupancy, occupancy_of(envelope, name))
        # The count has no user IDs, so a second read with them shows that the three own clients are counted.
        listed = await pubnub.here_now().channels(name).include_uuids(True).future()
        a.eq(own_occupants(listed, name, mine), sorted(mine), 'own occupants listed')
    await aeventually(check, what='here_now counts the three occupants')


async def test_here_now_groups(aclients):
    """Snippet: here_now_groups."""
    pubnub = aclients.asyncio('open', 'reader')
    groups = [n for n in ('cg1', 'cg2', 'cg3')]
    members = [(f'grouped_{i}') for i in (1, 2, 3)]
    for group, member in zip(groups, members):
        await pubnub.add_channel_to_channel_group().channels([member]).channel_group(group).future()
        live_cleanup.record('channel_group', group)
    one = aclients.asyncio('open', 'user_one')
    await alisten(one, *members)

    async def read():
        # snippet.here_now_groups
        envelope = await pubnub.here_now() \
            .channel_groups(['cg1', 'cg2', 'cg3']) \
            .include_uuids(True) \
            .include_state(True) \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        return envelope

    async def check():
        envelope = await read()
        a.eq(sorted((c.channel_name, own_occupants(envelope, c.channel_name, [one.uuid]))
                    for c in envelope.result.channels),
             sorted((m, [one.uuid]) for m in members), 'every channel of the groups with its occupant')
        a.eq(envelope.result.total_channels, 3)
        consistent(envelope)
    await aeventually(check, what='here_now by channel group')


async def test_where_now_self(aclients):
    """Snippets: where_now_self, where_now_other."""
    pubnub = aclients.asyncio('open', 'reader')
    first, second = 'my_channel', 'my_channel_2'
    await alisten(pubnub, first, second)
    other = aclients.asyncio('open', 'some-other-uuid')
    await alisten(other, first)

    async def own():
        # snippet.where_now_self
        envelope = await pubnub.where_now() \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        return envelope

    async def elsewhere():
        # snippet.where_now_other
        envelope = await pubnub.where_now() \
            .uuid('some-other-uuid') \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        return envelope

    async def check_own():
        a.eq(sorted((await own()).result.channels), sorted([first, second]), 'own channels')

    async def check_other():
        a.eq((await elsewhere()).result.channels, [first], 'channels of the other user ID')
    await aeventually(check_own)
    await aeventually(check_other)


async def test_set_state_builder(aclients):
    """Snippets: set_state_builder, get_state_builder."""
    pubnub = aclients.asyncio('open', 'such_uuid')
    reader = aclients.asyncio('open', 'reader')
    channels = [n for n in ('ch1', 'ch2', 'ch3')]
    await alisten(pubnub, *channels)

    # snippet.set_state_builder
    my_state = {
        'age': 20
    }
    envelope = await pubnub.set_state() \
        .channels(['ch1', 'ch2', 'ch3']) \
        .state(my_state) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    a.eq(envelope.result.state, {'age': 20}, 'state returned by set_state')

    # snippet.get_state_builder
    envelope = await pubnub.get_state() \
        .channels(['ch1', 'ch2', 'ch3']) \
        .uuid('such_uuid') \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    a.eq(envelope.result.channels, {c: {'age': 20} for c in channels}, 'state per channel')
    fetched = await reader.get_state().channels(channels[0]).uuid(pubnub.uuid).future()
    a.eq(fetched.result.channels, {channels[0]: {'age': 20}}, 'another client reads the state')


async def test_set_state_groups_builder(aclients):
    """Snippet: set_state_groups_builder."""
    pubnub = aclients.asyncio('open', 'such_uuid')
    groups = [n for n in ('gr1', 'gr2', 'gr3')]
    members = [(f'grouped_{i}') for i in (1, 2, 3)]
    own = 'ch1'
    for group, member in zip(groups, members):
        await pubnub.add_channel_to_channel_group().channels([member]).channel_group(group).future()
        live_cleanup.record('channel_group', group)
    await alisten(pubnub, own, *members, groups=groups)
    present([own, *members], pubnub.uuid)
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
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    a.eq(envelope.result.state, {'age': 20}, 'state returned by set_state for groups')
    own_state = await pubnub.get_state().channels(own).future()
    a.eq(own_state.result.channels, {own: {'age': 20}})

    async def group_state():
        # The presence service resolves a channel group some seconds after it was created, an error answers until then.
        envelope = await pubnub.get_state().channel_groups(groups).future()
        a.ok(not envelope.is_error() and envelope.result is not None, 'channel groups not resolved yet')
        return envelope.result.channels

    async def read_back():
        a.eq(await group_state(), {m: {'age': 20} for m in members}, 'state read back through the channel groups')

    await aeventually(read_back, timeout=45, what='state read back through the channel groups')
