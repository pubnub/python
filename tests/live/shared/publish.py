"""Scenario data and helpers of the publish page, shared by the sync and asyncio tests: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the tests call outside the snippet markers.
Coroutine twins of a sync helper carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from support import assertions as a

NAMES = []


async def history_of(pubnub, channel):
    fetched = await pubnub.fetch_messages(channels=[channel]).future()
    return [item.message for item in fetched.result.channels.get(channel, [])]


async def stored_has(pubnub, channel, wanted):
    a.contains(await history_of(pubnub, channel), wanted, 'message is stored in history')
