"""Docs page: channel groups (sync). Add, list, remove channels and delete the group.

Every step registers its group with the janitor and deletes it in a finally.
"""
from support import assertions as a
from support import cleanup as live_cleanup
from support.listen import listen
from support.wait import eventually
from shared.channel_groups import eventually_members, members


def test_add_channels_builder(clients):
    """Snippets: add_channels_builder, add_channels_named."""
    pubnub = clients.sync('open', 'grouper')
    group = 'cg1'
    channels = ['ch1', 'ch2']
    live_cleanup.record('channel_group', group)
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


def test_list_channels_builder(clients):
    """Snippets: list_channels_builder, list_channels_named."""
    pubnub = clients.sync('open', 'lister')
    group = 'cg1'
    channels = ['ch1', 'ch2']
    live_cleanup.record('channel_group', group)
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
        a.eq(members(pubnub, 'missing_group'), [], 'an unknown group is empty')
    finally:
        pubnub.remove_channel_group().channel_group(group).sync()


def test_remove_channels_builder(clients):
    """Snippets: remove_channels_builder, remove_channels_named."""
    pubnub = clients.sync('open', 'remover')
    group = 'channel_group'
    kids = ['son', 'daughter']
    pair = ['ch1', 'ch2']
    other_group = 'cg1'
    live_cleanup.record('channel_group', group)
    live_cleanup.record('channel_group', other_group)
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


def test_delete_channel_group_builder(clients):
    """Snippet: delete_channel_group_builder."""
    pubnub = clients.sync('open', 'deleter')
    group = 'cg1'
    channels = ['ch1', 'ch2']
    live_cleanup.record('channel_group', group)
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
