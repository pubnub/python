"""Docs page: presence (sync). Here now, where now and user state.

Presence needs channel tracking on the keyset. Joins of a second client are asserted, never the client's own join,
and here_now is polled with eventually because the service reports it with a delay and caches it for 3 seconds.
"""
from pubnub.exceptions import PubNubException

from support import assertions as a
from support import cleanup as live_cleanup
from support.listen import listen
from support.wait import PRESENCE_TIMEOUT, eventually
from shared.presence import Printed, consistent, occupancy_of, occupants_of, own_occupants


def test_here_now_builder(clients, capsys):
    """Snippets: here_now_builder, here_now_named."""
    pubnub = clients.sync('open', 'reader')
    first, second = 'my_channel', 'my_channel_2'
    printed = Printed(capsys)
    one = clients.sync('open', 'user_one')
    two = clients.sync('open', 'user_two')
    listen(one, first, second)
    listen(two, first)
    expected = {first: sorted([one.uuid, two.uuid]), second: [one.uuid]}

    def builder():
        # snippet.here_now_builder
        here_now = pubnub.here_now() \
            .channels(["my_channel", "my_channel_2"]) \
            .include_uuids(True) \
            .sync()

        if here_now.status.is_error():
            print(f"Error: {here_now.status.error}")
            return

        for channel_data in here_now.result.channels:
            print("---")
            print(f"Channel: {channel_data.channel_name}")
            print(f"Occupancy: {channel_data.occupancy}")
            for occupant in channel_data.occupants:
                print(f"UUID: {occupant.uuid}, State: {occupant.state}")
        # snippet.end
        return here_now

    def named():
        # snippet.here_now_named
        here_now = pubnub.here_now(
            channels=["my_channel", "my_channel_2"],
            include_uuids=True
        ).sync()

        if here_now.status.is_error():
            print(f"Error: {here_now.status.error}")
            return

        for channel_data in here_now.result.channels:
            print("---")
            print(f"Channel: {channel_data.channel_name}")
            print(f"Occupancy: {channel_data.occupancy}")
            for occupant in channel_data.occupants:
                print(f"UUID: {occupant.uuid}, State: {occupant.state}")
        # snippet.end
        return here_now

    for call in (builder, named):
        def check(call=call):
            result = call()
            a.ok(result is not None, 'here_now returned an error')
            a.eq({c: own_occupants(result, c, expected[c]) for c in expected}, expected, 'own occupants per channel')
            a.eq(result.result.total_channels, 2)
            consistent(result)
            return result
        last = eventually(check, what='here_now lists both clients')
    text = printed.text()
    a.contains(text, f'Channel: {first}\nOccupancy: {occupancy_of(last, first)}\n')
    a.contains(text, f'UUID: {one.uuid}, State: None')


def test_here_now_state(clients):
    """Snippet: here_now_state."""
    pubnub = clients.sync('open', 'reader')
    name = 'my_channel'
    one = clients.sync('open', 'user_one')
    listen(one, name)
    one.set_state().channels(name).state({'abcd': {'age': 15}}).sync()

    def read():
        # snippet.here_now_state
        envelope = pubnub.here_now() \
            .channels("my_channel") \
            .include_uuids(True) \
            .include_state(True) \
            .sync()
        # snippet.end
        return envelope

    def check():
        envelope = read()
        found = [(o.uuid, o.state) for c in envelope.result.channels for o in c.occupants]
        a.contains(found, (one.uuid, {'abcd': {'age': 15}}), 'own occupant with state')
        a.eq(envelope.result.total_channels, 1)
        consistent(envelope)
    eventually(check, what='here_now returns the state')


def test_here_now_occupancy(clients):
    """Snippet: here_now_occupancy."""
    pubnub = clients.sync('open', 'reader')
    name = 'my_channel'
    mine = ['user_one', 'user_two', 'user_three']
    for who in mine:
        listen(clients.sync('open', who), name)

    def read():
        # snippet.here_now_occupancy
        envelope = pubnub.here_now() \
            .channels("my_channel") \
            .include_uuids(False) \
            .include_state(False) \
            .sync()
        # snippet.end
        return envelope

    def check():
        envelope = read()
        a.eq([(c.channel_name, c.occupants) for c in envelope.result.channels], [(name, [])], 'no user IDs')
        a.ok(occupancy_of(envelope, name) >= len(mine), 'the count includes the three own occupants')
        a.eq(envelope.result.total_occupancy, occupancy_of(envelope, name))
        # The count has no user IDs, so a second read with them shows that the three own clients are counted.
        listed = pubnub.here_now().channels(name).include_uuids(True).sync()
        a.eq(own_occupants(listed, name, mine), sorted(mine), 'own occupants listed')
    eventually(check, what='here_now counts the three occupants')


def test_here_now_groups(clients):
    """Snippet: here_now_groups."""
    pubnub = clients.sync('open', 'reader')
    groups = [n for n in ('cg1', 'cg2', 'cg3')]
    members = [(f'grouped_{i}') for i in (1, 2, 3)]
    for group, member in zip(groups, members):
        pubnub.add_channel_to_channel_group().channels([member]).channel_group(group).sync()
        live_cleanup.record('channel_group', group)
    one = clients.sync('open', 'user_one')
    listen(one, *members)

    def read():
        # snippet.here_now_groups
        envelope = pubnub.here_now() \
            .channel_groups(['cg1', 'cg2', 'cg3']) \
            .include_uuids(True) \
            .include_state(True) \
            .sync()
        # snippet.end
        return envelope

    def check():
        envelope = read()
        a.eq(sorted((c.channel_name, own_occupants(envelope, c.channel_name, [one.uuid]))
                    for c in envelope.result.channels),
             sorted((m, [one.uuid]) for m in members), 'every channel of the groups with its occupant')
        a.eq(envelope.result.total_channels, 3)
        consistent(envelope)
    eventually(check, what='here_now by channel group')


def test_here_now_paginate(clients):
    """Snippet: here_now_paginate."""
    pubnub = clients.sync('open', 'reader')
    name = 'my_channel'
    users = [clients.sync('open', who) for who in ('user_one', 'user_two', 'user_three')]
    for user in users:
        listen(user, name)
    everyone = sorted(user.uuid for user in users)

    def read():
        # snippet.here_now_paginate
        # Get first 10 occupants
        envelope = pubnub.here_now() \
            .channels("my_channel") \
            .limit(10) \
            .sync()

        # Get next 10 occupants (starting from position 10)
        envelope = pubnub.here_now() \
            .channels("my_channel") \
            .limit(10) \
            .offset(10) \
            .sync()
        # snippet.end
        return envelope

    def check():
        # Other user IDs can still be listed on the shared channel (see own_occupants), so the page sizes follow the
        # occupancy the same response reports, and the own clients must be on the pages.
        rest = read()
        a.eq(len(occupants_of(rest, name) or []), max(0, occupancy_of(rest, name) - 10), 'from position 10 on')
        all_in_ten = pubnub.here_now().channels(name).limit(10).sync()
        a.eq(own_occupants(all_in_ten, name, everyone), everyone, 'limit 10 lists the three own clients')
    eventually(check, what='here_now pagination')

    def paged():
        total = occupancy_of(pubnub.here_now().channels(name).limit(2).sync(), name)
        pages = []
        for offset in range(0, total, 2):
            page = pubnub.here_now().channels(name).limit(2).offset(offset).sync()
            a.eq(occupancy_of(page, name), total, 'occupancy counts all occupants on every page')
            pages.append(occupants_of(page, name) or [])
        a.eq([len(p) for p in pages], [min(2, total - o) for o in range(0, total, 2)], 'page sizes')
        merged = [u for p in pages for u in p]
        a.eq(len(merged), len(set(merged)), 'pages list every occupant once')
        a.eq(sorted(set(merged) & set(everyone)), everyone, 'pages cover every own occupant')
    eventually(paged, timeout=PRESENCE_TIMEOUT, what='here_now pages')


def test_where_now_self(clients):
    """Snippets: where_now_self, where_now_other_builder, where_now_other_named."""
    pubnub = clients.sync('open', 'reader')
    first, second = 'my_channel', 'my_channel_2'
    listen(pubnub, first, second)
    other = clients.sync('open', 'some-other-uuid')
    listen(other, first)

    def own():
        # snippet.where_now_self
        envelope = pubnub.where_now().sync()
        # snippet.end
        return envelope

    def builder():
        # snippet.where_now_other_builder
        envelope = pubnub.where_now() \
            .uuid('some-other-uuid') \
            .sync()
        # snippet.end
        return envelope

    def named():
        # snippet.where_now_other_named
        envelope = pubnub.where_now(user_id='some-other-uuid').sync()
        # snippet.end
        return envelope

    eventually(lambda: a.eq(sorted(own().result.channels), sorted([first, second]), 'own channels'))
    eventually(lambda: a.eq(builder().result.channels, [first], 'channels of the other user ID (builder)'))
    eventually(lambda: a.eq(named().result.channels, [first], 'channels of the other user ID (named)'))


def test_set_state_builder(clients):
    """Snippets: set_state_builder, set_state_named, get_state_builder, get_state_named."""
    pubnub = clients.sync('open', 'such_uuid')
    reader = clients.sync('open', 'reader')
    channels = [n for n in ('ch1', 'ch2', 'ch3')]
    listen(pubnub, *channels)

    # snippet.set_state_builder
    my_state = {
        'age': 20
    }
    envelope = pubnub.set_state() \
        .channels(['ch1', 'ch2', 'ch3']) \
        .state(my_state) \
        .sync()
    # snippet.end
    a.eq(envelope.result.state, {'age': 20}, 'state returned by set_state (builder)')

    # snippet.set_state_named
    envelope = pubnub.set_state(channels=['ch1', 'ch2', 'ch3'], state={'age': 21}).sync()
    # snippet.end
    a.eq(envelope.result.state, {'age': 21}, 'state returned by set_state (named)')

    # snippet.get_state_builder
    envelope = pubnub.get_state() \
        .channels(['ch1', 'ch2', 'ch3']) \
        .uuid('such_uuid') \
        .sync()
    # snippet.end
    a.eq(envelope.result.channels, {c: {'age': 21} for c in channels}, 'state per channel (builder)')

    # snippet.get_state_named
    envelope = pubnub.get_state(channels=['ch1', 'ch2', 'ch3'], uuid='such_uuid').sync()
    # snippet.end
    a.eq(envelope.result.channels, {c: {'age': 21} for c in channels}, 'state per channel (named)')
    a.eq(reader.get_state().channels(channels[0]).uuid(pubnub.uuid).sync().result.channels,
         {channels[0]: {'age': 21}}, 'another client reads the state')


def test_set_state_groups_builder(clients):
    """Snippets: set_state_groups_builder, set_state_groups_named."""
    pubnub = clients.sync('open', 'such_uuid')
    groups = [n for n in ('gr1', 'gr2', 'gr3')]
    members = [(f'grouped_{i}') for i in (1, 2, 3)]
    own = 'ch1'
    for group, member in zip(groups, members):
        pubnub.add_channel_to_channel_group().channels([member]).channel_group(group).sync()
        live_cleanup.record('channel_group', group)
    listen(pubnub, own, *members, groups=groups)
    # The SDK refuses a set_state() that names channel groups and no channel (PubNubException "State setter for
    # channel groups is not supported yet"), so the samples below add a channel next to the groups.
    refusal = a.raises(PubNubException, lambda: pubnub.set_state().channel_groups(groups).state({'age': 20}).sync())
    a.contains(str(refusal), 'State setter for channel groups is not supported yet')

    # snippet.set_state_groups_builder
    my_state = {
        'age': 20
    }
    envelope = pubnub.set_state() \
        .channels(['ch1']) \
        .channel_groups(['gr1', 'gr2', 'gr3']) \
        .state(my_state) \
        .sync()
    # snippet.end
    a.eq(envelope.result.state, {'age': 20}, 'state returned by set_state for groups (builder)')
    a.eq(pubnub.get_state().channels(own).sync().result.channels, {own: {'age': 20}})

    # snippet.set_state_groups_named
    envelope = pubnub.set_state(channels=['ch1'], channel_groups=['gr1', 'gr2', 'gr3'], state={'age': 22}).sync()
    # snippet.end
    a.eq(envelope.result.state, {'age': 22}, 'state returned by set_state for groups (named)')
    a.eq(pubnub.get_state().channels(own).sync().result.channels, {own: {'age': 22}})

    def group_state():
        # The presence service resolves a channel group some seconds after it was created and answers 400 until then.
        try:
            return pubnub.get_state().channel_groups(groups).sync().result.channels
        except PubNubException as error:
            raise AssertionError(f'channel groups not resolved yet: {error}')

    eventually(lambda: a.eq(group_state(), {m: {'age': 22} for m in members}, 'state read back through the groups'),
               timeout=45, what='state read back through the channel groups')
