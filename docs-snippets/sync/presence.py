"""Docs page: presence (sync). Here now, where now and user state.

Presence needs channel tracking on the keyset. Joins of a second client are asserted, never the client's own join,
and here_now is polled with eventually because the service reports it with a delay and caches it for 3 seconds.
"""
from pubnub.exceptions import PubNubException

from harness import assertions as a
from harness import names
from harness import world
from harness.listeners import listen
from harness.step import step
from harness.wait import eventually

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


@step('here_now_builder', 'here_now_named', role='open')
def test_here_now(clients, capsys):
    pubnub = clients.sync('open', 'reader')
    first, second = names.with_suffix('my_channel'), names.with_suffix('my_channel_2')
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
            a.eq({c: occupants_of(result, c) for c in expected}, expected, 'occupants per channel')
            a.eq((result.result.total_channels, result.result.total_occupancy), (2, 3))
        eventually(check, what='here_now lists both clients')
    text = printed.text()
    a.contains(text, f'Channel: {first}\nOccupancy: 2\n')
    a.contains(text, f'UUID: {one.uuid}, State: None')


@step('here_now_state', role='open')
def test_here_now_state(clients):
    pubnub = clients.sync('open', 'reader')
    name = names.with_suffix('my_channel')
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
        a.eq(found, [(one.uuid, {'abcd': {'age': 15}})], 'occupants with state')
        a.eq((envelope.result.total_channels, envelope.result.total_occupancy), (1, 1))
    eventually(check, what='here_now returns the state')


@step('here_now_occupancy', role='open')
def test_here_now_occupancy(clients):
    pubnub = clients.sync('open', 'reader')
    name = names.with_suffix('my_channel')
    for who in ('user_one', 'user_two', 'user_three'):
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
        a.eq([(c.channel_name, c.occupancy, c.occupants) for c in envelope.result.channels], [(name, 3, [])])
        a.eq((envelope.result.total_channels, envelope.result.total_occupancy), (1, 3))
    eventually(check, what='here_now counts three occupants')


@step('here_now_groups', role='open')
def test_here_now_groups(clients):
    pubnub = clients.sync('open', 'reader')
    groups = [names.with_suffix(n) for n in ('cg1', 'cg2', 'cg3')]
    members = [names.with_suffix(f'grouped_{i}') for i in (1, 2, 3)]
    for group, member in zip(groups, members):
        pubnub.add_channel_to_channel_group().channels([member]).channel_group(group).sync()
        world.record('channel_group', group)
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
        a.eq(sorted((c.channel_name, c.occupancy, [o.uuid for o in c.occupants]) for c in envelope.result.channels),
             sorted((m, 1, [one.uuid]) for m in members), 'every channel of the groups with its occupant')
        a.eq((envelope.result.total_channels, envelope.result.total_occupancy), (3, 3))
    eventually(check, what='here_now by channel group')


@step('here_now_paginate', role='open')
def test_here_now_paginate(clients):
    pubnub = clients.sync('open', 'reader')
    name = names.with_suffix('my_channel')
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
        a.eq(occupants_of(read(), name), [], 'nothing from position 10 on')
        all_in_ten = pubnub.here_now().channels(name).limit(10).sync()
        a.eq(occupants_of(all_in_ten, name), everyone, 'limit 10 returns all three')
    eventually(check, what='here_now pagination')
    pages = []
    for offset in (0, 2):
        page = pubnub.here_now().channels(name).limit(2).offset(offset).sync()
        pages.append(occupants_of(page, name))
        a.eq(occupancy_of(page, name), 3, 'occupancy counts all occupants on every page')
    a.eq((len(pages[0]), len(pages[1])), (2, 1))
    a.eq(sorted(pages[0] + pages[1]), everyone, 'pages cover every occupant once')


@step('where_now_self', 'where_now_other_builder', 'where_now_other_named', role='open')
def test_where_now(clients):
    pubnub = clients.sync('open', 'reader')
    first, second = names.with_suffix('my_channel'), names.with_suffix('my_channel_2')
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


@step('set_state_builder', 'set_state_named', 'get_state_builder', 'get_state_named', role='open')
def test_state(clients):
    pubnub = clients.sync('open', 'such_uuid')
    reader = clients.sync('open', 'reader')
    channels = [names.with_suffix(n) for n in ('ch1', 'ch2', 'ch3')]
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


@step('set_state_groups_builder', 'set_state_groups_named', role='open')
def test_state_for_groups(clients):
    pubnub = clients.sync('open', 'such_uuid')
    groups = [names.with_suffix(n) for n in ('gr1', 'gr2', 'gr3')]
    members = [names.with_suffix(f'grouped_{i}') for i in (1, 2, 3)]
    own = names.with_suffix('ch1')
    for group, member in zip(groups, members):
        pubnub.add_channel_to_channel_group().channels([member]).channel_group(group).sync()
        world.record('channel_group', group)
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
