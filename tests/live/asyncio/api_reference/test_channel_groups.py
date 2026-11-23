"""Docs page: channel groups (asyncio). Same steps as sync/channel_groups.py with await.

Every step registers its group with the janitor and deletes it in a finally.
"""
from support import assertions as a
from support import cleanup as live_cleanup
from support.listen import alisten
from support.wait import aeventually
from shared.channel_groups import eventually_members_async as eventually_members, members_async as members


async def test_add_channels_builder(aclients):
    """Snippets: add_channels_builder, add_channels_named."""
    pubnub = aclients.asyncio('open', 'grouper')
    group = 'cg1'
    channels = ['ch1', 'ch2']
    live_cleanup.record('channel_group', group)
    try:
        # snippet.add_channels_builder
        envelope = await pubnub.add_channel_to_channel_group() \
            .channels(["ch1", "ch2"]) \
            .channel_group("cg1") \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
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
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        await eventually_members(pubnub, group, channels)
    finally:
        await pubnub.remove_channel_group().channel_group(group).future()


async def test_list_channels_builder(aclients):
    """Snippets: list_channels_builder, list_channels_named."""
    pubnub = aclients.asyncio('open', 'lister')
    group = 'cg1'
    channels = ['ch1', 'ch2']
    live_cleanup.record('channel_group', group)
    try:
        await pubnub.add_channel_to_channel_group().channels(channels).channel_group(group).future()
        await eventually_members(pubnub, group, channels)

        # snippet.list_channels_builder
        envelope = await pubnub.list_channels_in_channel_group() \
            .channel_group("cg1") \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        else:
            print(envelope.result.channels)
        # snippet.end
        a.eq(sorted(envelope.result.channels), channels)
        a.eq(type(envelope.result.channels), list, 'channels is a list, not a dictionary')

        # snippet.list_channels_named
        envelope = await pubnub.list_channels_in_channel_group(channel_group="cg1").future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        a.eq(sorted(envelope.result.channels), channels)
        a.eq(await members(pubnub, 'missing_group'), [], 'an unknown group is empty')
    finally:
        await pubnub.remove_channel_group().channel_group(group).future()


async def test_remove_channels_builder(aclients):
    """Snippets: remove_channels_builder, remove_channels_named."""
    pubnub = aclients.asyncio('open', 'remover')
    group = 'channel_group'
    kids = ['son', 'daughter']
    pair = ['ch1', 'ch2']
    other_group = 'cg1'
    live_cleanup.record('channel_group', group)
    live_cleanup.record('channel_group', other_group)
    try:
        await pubnub.add_channel_to_channel_group().channels(kids + pair).channel_group(group).future()
        await pubnub.add_channel_to_channel_group().channels(pair).channel_group(other_group).future()
        await eventually_members(pubnub, group, kids + pair)

        # snippet.remove_channels_builder
        envelope = await pubnub.remove_channel_from_channel_group() \
            .channels(["son", "daughter"]) \
            .channel_group("channel_group") \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        a.eq(str(envelope.result), 'Channel successfully removed')
        await eventually_members(pubnub, group, pair)

        # snippet.remove_channels_named
        envelope = await pubnub.remove_channel_from_channel_group(channels=["ch1", "ch2"],
                                                                  channel_group="cg1").future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        await eventually_members(pubnub, other_group, [])
        a.eq(await members(pubnub, group), sorted(pair), 'the other group is untouched')
    finally:
        await pubnub.remove_channel_group().channel_group(group).future()
        await pubnub.remove_channel_group().channel_group(other_group).future()


async def test_delete_channel_group_builder(aclients):
    """Snippet: delete_channel_group_builder."""
    pubnub = aclients.asyncio('open', 'deleter')
    group = 'cg1'
    channels = ['ch1', 'ch2']
    live_cleanup.record('channel_group', group)
    try:
        await pubnub.add_channel_to_channel_group().channels(channels).channel_group(group).future()
        await eventually_members(pubnub, group, channels)

        # snippet.delete_channel_group_builder
        envelope = await pubnub.remove_channel_group() \
            .channel_group("cg1") \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        a.eq(envelope.status.is_error(), False)
        a.eq(str(envelope.result), 'Group successfully removed')
        await eventually_members(pubnub, group, [])
        # The docs show remove_channel_group(channel_group="cg1"), but the method takes no argument
        a.raises(TypeError, lambda: pubnub.remove_channel_group(channel_group=group))
    finally:
        await pubnub.remove_channel_group().channel_group(group).future()
