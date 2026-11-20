"""Docs page: channel groups (asyncio). Same steps as sync/channel_groups.py with await.

Every step registers its group with the janitor and deletes it in a finally.
"""
from harness import assertions as a
from harness import names, world
from harness.listeners import alisten
from harness.step import step
from harness.wait import aeventually

REGISTERED_NAMES = ['son', 'daughter', 'channel_group']


async def members(client, group):
    envelope = await client.list_channels_in_channel_group().channel_group(group).future()
    return sorted(envelope.result.channels)


async def eventually_members(client, group, expected):
    async def check():
        a.eq(await members(client, group), sorted(expected), 'channels in the group')

    await aeventually(check, timeout=30, what='group membership')


@step('add_channels_builder', 'add_channels_named', role='open')
async def test_add_channels(aclients):
    pubnub = aclients.asyncio('open', 'grouper')
    group = names.with_suffix('cg1')
    channels = [names.with_suffix('ch1'), names.with_suffix('ch2')]
    world.record('channel_group', group)
    try:
        # snippet.add_channels_builder
        envelope = await pubnub.add_channel_to_channel_group() \
            .channels(["ch1", "ch2"]) \
            .channel_group("cg1") \
            .future()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        a.eq(str(envelope.result), 'Channel successfully added')
        await eventually_members(pubnub, group, channels)

        # A subscriber on the group receives a publish to a member channel
        seen = await alisten(aclients.asyncio('open', 'member_listener'), groups=[group])
        await pubnub.publish().channel(channels[0]).message('to-member').future()
        await aeventually(lambda: a.eq([m.message for m in seen.messages], ['to-member'], 'group message received'))
        a.eq((seen.messages[0].channel, seen.messages[0].subscription), (channels[0], group))

        await pubnub.remove_channel_from_channel_group().channels(channels).channel_group(group).future()
        await eventually_members(pubnub, group, [])

        # snippet.add_channels_named
        envelope = await pubnub.add_channel_to_channel_group(channels=["ch1", "ch2"], channel_group="cg1").future()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        await eventually_members(pubnub, group, channels)
    finally:
        await pubnub.remove_channel_group().channel_group(group).future()


@step('list_channels_builder', 'list_channels_named', role='open')
async def test_list_channels(aclients):
    pubnub = aclients.asyncio('open', 'lister')
    group = names.with_suffix('cg1')
    channels = [names.with_suffix('ch1'), names.with_suffix('ch2')]
    world.record('channel_group', group)
    try:
        await pubnub.add_channel_to_channel_group().channels(channels).channel_group(group).future()
        await eventually_members(pubnub, group, channels)

        # snippet.list_channels_builder
        envelope = await pubnub.list_channels_in_channel_group() \
            .channel_group("cg1") \
            .future()
        print(envelope.result.channels)
        # snippet.end
        a.eq(sorted(envelope.result.channels), channels)
        a.eq(type(envelope.result.channels), list, 'channels is a list, not a dictionary')

        # snippet.list_channels_named
        envelope = await pubnub.list_channels_in_channel_group(channel_group="cg1").future()
        # snippet.end
        a.eq(sorted(envelope.result.channels), channels)
        a.eq(await members(pubnub, names.with_suffix('missing_group')), [], 'an unknown group is empty')
    finally:
        await pubnub.remove_channel_group().channel_group(group).future()


@step('remove_channels_builder', 'remove_channels_named', role='open')
async def test_remove_channels(aclients):
    pubnub = aclients.asyncio('open', 'remover')
    group = names.with_suffix('channel_group')
    kids = [names.with_suffix('son'), names.with_suffix('daughter')]
    pair = [names.with_suffix('ch1'), names.with_suffix('ch2')]
    other_group = names.with_suffix('cg1')
    world.record('channel_group', group)
    world.record('channel_group', other_group)
    try:
        await pubnub.add_channel_to_channel_group().channels(kids + pair).channel_group(group).future()
        await pubnub.add_channel_to_channel_group().channels(pair).channel_group(other_group).future()
        await eventually_members(pubnub, group, kids + pair)

        # snippet.remove_channels_builder
        envelope = await pubnub.remove_channel_from_channel_group() \
            .channels(["son", "daughter"]) \
            .channel_group("channel_group") \
            .future()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        a.eq(str(envelope.result), 'Channel successfully removed')
        await eventually_members(pubnub, group, pair)

        # snippet.remove_channels_named
        envelope = await pubnub.remove_channel_from_channel_group(channels=["ch1", "ch2"],
                                                                  channel_group="cg1").future()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        await eventually_members(pubnub, other_group, [])
        a.eq(await members(pubnub, group), sorted(pair), 'the other group is untouched')
    finally:
        await pubnub.remove_channel_group().channel_group(group).future()
        await pubnub.remove_channel_group().channel_group(other_group).future()


@step('delete_channel_group_builder', role='open')
async def test_delete_channel_group(aclients):
    pubnub = aclients.asyncio('open', 'deleter')
    group = names.with_suffix('cg1')
    channels = [names.with_suffix('ch1'), names.with_suffix('ch2')]
    world.record('channel_group', group)
    try:
        await pubnub.add_channel_to_channel_group().channels(channels).channel_group(group).future()
        await eventually_members(pubnub, group, channels)

        # snippet.delete_channel_group_builder
        envelope = await pubnub.remove_channel_group() \
            .channel_group("cg1") \
            .future()
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        a.eq(str(envelope.result), 'Group successfully removed')
        await eventually_members(pubnub, group, [])
        # The docs show remove_channel_group(channel_group="cg1"), but the method takes no argument
        a.raises(TypeError, lambda: pubnub.remove_channel_group(channel_group=group))
    finally:
        await pubnub.remove_channel_group().channel_group(group).future()
