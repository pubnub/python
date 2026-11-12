"""Docs page: channel groups (sync). Add, list, remove channels and delete the group.

Every step registers its group with the janitor and deletes it in a finally.
"""
from harness import assertions as a
from harness import names, world
from harness.listeners import listen
from harness.step import step
from harness.wait import eventually

REGISTERED_NAMES = ['son', 'daughter', 'channel_group']


def members(client, group):
    return sorted(client.list_channels_in_channel_group().channel_group(group).sync().result.channels)


def eventually_members(client, group, expected):
    eventually(lambda: a.eq(members(client, group), sorted(expected), 'channels in the group'), timeout=30,
               what='group membership')


@step('add_channels_builder', 'add_channels_named', role='open')
def test_add_channels(clients):
    pubnub = clients.sync('open', 'grouper')
    group = names.with_suffix('cg1')
    channels = [names.with_suffix('ch1'), names.with_suffix('ch2')]
    world.record('channel_group', group)
    try:
        # snippet.add_channels_builder
        envelope = pubnub.add_channel_to_channel_group() \
            .channels(["ch1", "ch2"]) \
            .channel_group("cg1") \
            .sync()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        a.eq(str(envelope.result), 'Channel successfully added')
        eventually_members(pubnub, group, channels)

        # A subscriber on the group receives a publish to a member channel
        seen = listen(clients.sync('open', 'member_listener'), groups=[group])
        pubnub.publish().channel(channels[0]).message('to-member').sync()
        eventually(lambda: a.eq([m.message for m in seen.messages], ['to-member'], 'group message received'))
        a.eq((seen.messages[0].channel, seen.messages[0].subscription), (channels[0], group))

        pubnub.remove_channel_from_channel_group().channels(channels).channel_group(group).sync()
        eventually_members(pubnub, group, [])

        # snippet.add_channels_named
        envelope = pubnub.add_channel_to_channel_group(channels=["ch1", "ch2"], channel_group="cg1").sync()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        eventually_members(pubnub, group, channels)
    finally:
        pubnub.remove_channel_group().channel_group(group).sync()


@step('list_channels_builder', 'list_channels_named', role='open')
def test_list_channels(clients):
    pubnub = clients.sync('open', 'lister')
    group = names.with_suffix('cg1')
    channels = [names.with_suffix('ch1'), names.with_suffix('ch2')]
    world.record('channel_group', group)
    try:
        pubnub.add_channel_to_channel_group().channels(channels).channel_group(group).sync()
        eventually_members(pubnub, group, channels)

        # snippet.list_channels_builder
        result = pubnub.list_channels_in_channel_group() \
            .channel_group("cg1") \
            .sync()
        print(result.result.channels)
        # snippet.end
        a.eq(sorted(result.result.channels), channels)
        a.eq(type(result.result.channels), list, 'channels is a list, not a dictionary')

        # snippet.list_channels_named
        result = pubnub.list_channels_in_channel_group(channel_group="cg1").sync()
        # snippet.end
        a.eq(sorted(result.result.channels), channels)
        a.eq(members(pubnub, names.with_suffix('missing_group')), [], 'an unknown group is empty')
    finally:
        pubnub.remove_channel_group().channel_group(group).sync()


@step('remove_channels_builder', 'remove_channels_named', role='open')
def test_remove_channels(clients):
    pubnub = clients.sync('open', 'remover')
    group = names.with_suffix('channel_group')
    kids = [names.with_suffix('son'), names.with_suffix('daughter')]
    pair = [names.with_suffix('ch1'), names.with_suffix('ch2')]
    other_group = names.with_suffix('cg1')
    world.record('channel_group', group)
    world.record('channel_group', other_group)
    try:
        pubnub.add_channel_to_channel_group().channels(kids + pair).channel_group(group).sync()
        pubnub.add_channel_to_channel_group().channels(pair).channel_group(other_group).sync()
        eventually_members(pubnub, group, kids + pair)

        # snippet.remove_channels_builder
        envelope = pubnub.remove_channel_from_channel_group() \
            .channels(["son", "daughter"]) \
            .channel_group("channel_group") \
            .sync()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        a.eq(str(envelope.result), 'Channel successfully removed')
        eventually_members(pubnub, group, pair)

        # snippet.remove_channels_named
        envelope = pubnub.remove_channel_from_channel_group(channels=["ch1", "ch2"], channel_group="cg1").sync()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        eventually_members(pubnub, other_group, [])
        a.eq(members(pubnub, group), sorted(pair), 'the other group is untouched')
    finally:
        pubnub.remove_channel_group().channel_group(group).sync()
        pubnub.remove_channel_group().channel_group(other_group).sync()


@step('delete_channel_group_builder', role='open')
def test_delete_channel_group(clients):
    pubnub = clients.sync('open', 'deleter')
    group = names.with_suffix('cg1')
    channels = [names.with_suffix('ch1'), names.with_suffix('ch2')]
    world.record('channel_group', group)
    try:
        pubnub.add_channel_to_channel_group().channels(channels).channel_group(group).sync()
        eventually_members(pubnub, group, channels)

        # snippet.delete_channel_group_builder
        envelope = pubnub.remove_channel_group() \
            .channel_group("cg1") \
            .sync()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        a.eq(str(envelope.result), 'Group successfully removed')
        eventually_members(pubnub, group, [])

        # The docs show remove_channel_group(channel_group="cg1"), but the method takes no argument
        a.raises(TypeError, lambda: pubnub.remove_channel_group(channel_group=group))
    finally:
        pubnub.remove_channel_group().channel_group(group).sync()
