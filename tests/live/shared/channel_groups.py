"""Shared scenario data of the channel-groups page for both docsets: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the sync and asyncio tests call outside
the snippet markers. Moved from the old docs-snippets/<docset>/ modules. Coroutine twins of a sync helper
carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from support import assertions as a
from support.wait import asettled, settled

NAMES = ['channel_group', 'daughter', 'missing_group', 'son']


def members(client, group):
    return sorted(client.list_channels_in_channel_group().channel_group(group).sync().result.channels)


def eventually_members(client, group, expected):
    """The group lists exactly `expected` on consecutive reads. A precondition that passes once can still be stale
    on the next read (the sample's), and a later exact read must not see the state before a write."""
    settled(lambda: a.eq(members(client, group), sorted(expected), 'channels in the group'), timeout=30,
            what='group membership')


async def members_async(client, group):
    envelope = await client.list_channels_in_channel_group().channel_group(group).future()
    return sorted(envelope.result.channels)


async def eventually_members_async(client, group, expected):
    async def check():
        a.eq(await members_async(client, group), sorted(expected), 'channels in the group')

    await asettled(check, timeout=30, what='group membership')
