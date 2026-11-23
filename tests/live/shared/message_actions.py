"""Shared scenario data of the message-actions page for both docsets: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the sync and asyncio tests call outside
the snippet markers. Moved from the old docs-snippets/<docset>/ modules. Coroutine twins of a sync helper
carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from pubnub.models.consumer.message_actions import PNMessageAction

from support import assertions as a
from support.wait import eventually
from support.wait import aeventually

NAMES = ['chats.room1']


def publish_stored(client, channel, count=1):
    """Publish count messages and wait until history returns them. Returns their timetokens, oldest first."""
    tokens = [int(client.publish().channel(channel).message({'n': i}).sync().result.timetoken) for i in range(count)]

    def stored():
        got = client.fetch_messages(channels=[channel], start=tokens[-1] + 1, end=tokens[0]).sync()
        a.eq([int(i.timetoken) for i in got.result.channels.get(channel, [])], tokens, 'stored timetokens')

    eventually(stored, timeout=30, what='published messages stored')
    return tokens


def add_action(client, channel, message_timetoken, value, action_type='reaction'):
    action = PNMessageAction()
    action.type = action_type
    action.value = value
    action.message_timetoken = message_timetoken
    return client.add_message_action().channel(channel).message_action(action).sync().result


async def publish_stored_async(client, channel, count=1):
    """Publish count messages and wait until history returns them. Returns their timetokens, oldest first."""
    tokens = []
    for i in range(count):
        envelope = await client.publish().channel(channel).message({'n': i}).future()
        tokens.append(int(envelope.result.timetoken))

    async def stored():
        got = await client.fetch_messages(channels=[channel], start=tokens[-1] + 1, end=tokens[0]).future()
        a.eq([int(i.timetoken) for i in got.result.channels.get(channel, [])], tokens, 'stored timetokens')

    await aeventually(stored, timeout=30, what='published messages stored')
    return tokens


async def add_action_async(client, channel, message_timetoken, value, action_type='reaction'):
    action = PNMessageAction()
    action.type = action_type
    action.value = value
    action.message_timetoken = message_timetoken
    return (await client.add_message_action().channel(channel).message_action(action).future()).result


async def remove_action(client, channel, message_timetoken, action_timetoken):
    await client.remove_message_action(channel=channel, message_timetoken=message_timetoken,
                                       action_timetoken=int(action_timetoken)).future()
