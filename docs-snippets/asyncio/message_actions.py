"""Docs page: message actions (asyncio). Same steps as sync/message_actions.py with await.

A message action needs a stored message, so every step waits until the published message is readable from history.
"""
from pubnub.models.consumer.message_actions import PNMessageAction

from harness import assertions as a
from harness import names
from harness.listeners import alisten
from harness.step import step
from harness.wait import aeventually

REGISTERED_NAMES = ['chats.room1']


async def publish_stored(client, channel, count=1):
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


async def add_action(client, channel, message_timetoken, value, action_type='reaction'):
    action = PNMessageAction()
    action.type = action_type
    action.value = value
    action.message_timetoken = message_timetoken
    return (await client.add_message_action().channel(channel).message_action(action).future()).result


async def remove_action(client, channel, message_timetoken, action_timetoken):
    await client.remove_message_action(channel=channel, message_timetoken=message_timetoken,
                                       action_timetoken=int(action_timetoken)).future()


@step('add_message_action_builder', 'add_message_action_named', role='open')
async def test_add_message_action(aclients):
    pubnub = aclients.asyncio('open', 'reactor')
    channel = names.with_suffix('chats.room1')
    seen = await alisten(aclients.asyncio('open', 'watcher'), channel)
    message_timetoken = (await publish_stored(pubnub, channel))[0]

    # snippet.add_message_action_builder
    # snippet.hide
    from pubnub.models.consumer.message_actions import PNMessageAction
    # snippet.show
    msg_action = PNMessageAction()
    msg_action.type = "reaction"
    msg_action.value = "smiley_face"
    msg_action.message_timetoken = message_timetoken

    envelope = await pubnub.add_message_action() \
        .channel("chats.room1") \
        .message_action(msg_action) \
        .future()

    print(f"Added action at timetoken: {envelope.result.action_timetoken}")
    # snippet.end

    added = envelope.result
    a.eq(envelope.status.is_error(), False)
    a.timetoken(added.action_timetoken)
    a.eq((added.type, added.value, added.uuid), ('reaction', 'smiley_face', pubnub.uuid))
    a.eq(int(added.message_timetoken), message_timetoken)
    await aeventually(lambda: a.eq(len(seen.message_actions), 1, 'action events received'))
    event = seen.message_actions[0]
    a.eq((event.type, event.value, event.uuid), ('reaction', 'smiley_face', pubnub.uuid))
    a.eq(event.action_timetoken, added.action_timetoken)
    a.eq(int(event.message_timetoken), message_timetoken)
    a.eq(event.channel, channel)

    # snippet.add_message_action_named
    msg_action = PNMessageAction()
    msg_action.type = "reaction"
    msg_action.value = "thumbs_up"
    msg_action.message_timetoken = message_timetoken

    envelope = await pubnub.add_message_action(
        channel="chats.room1",
        message_action=msg_action
    ).future()

    print(f"Added action at timetoken: {envelope.result.action_timetoken}")
    # snippet.end
    a.eq(envelope.result.value, 'thumbs_up')

    async def read_back():
        got = await pubnub.fetch_messages(channels=[channel], count=1, include_message_actions=True).future()
        actions = got.result.channels[channel][0].actions
        a.eq(sorted(actions['reaction']), ['smiley_face', 'thumbs_up'], 'fetch shows both actions')
        a.eq(actions['reaction']['smiley_face'][0]['actionTimetoken'], added.action_timetoken)
        a.eq(actions['reaction']['smiley_face'][0]['uuid'], pubnub.uuid)

    await aeventually(read_back, timeout=30, what='actions visible through fetch_messages')
    await aeventually(lambda: a.eq(len(seen.message_actions), 2, 'second action event received'))
    for action_timetoken in (added.action_timetoken, envelope.result.action_timetoken):
        await remove_action(pubnub, channel, message_timetoken, action_timetoken)


@step('get_message_actions_builder', 'get_message_actions_named', role='open')
async def test_get_message_actions(aclients):
    pubnub = aclients.asyncio('open', 'reader')
    channel = names.with_suffix('chats.room1')
    tokens = await publish_stored(pubnub, channel, 3)
    first, second, third = [(await add_action(pubnub, channel, tt, 'smiley_face')).action_timetoken for tt in tokens]
    a.ok(first < second < third, 'action timetokens grow')

    async def all_visible():
        got = (await pubnub.get_message_actions(channel=channel).future()).result.actions
        mine = [x.action_timetoken for x in got if int(x.message_timetoken) in tokens]
        a.eq(mine, [first, second, third], 'ascending by action timetoken')

    await aeventually(all_visible, timeout=30, what='actions listed')
    start, end = str(third), str(second)

    # snippet.get_message_actions_builder
    envelope = await pubnub.get_message_actions() \
        .channel("chats.room1") \
        .start(start) \
        .end(end) \
        .limit("50") \
        .future()

    for action in envelope.result.actions:
        print(f"Message Action type: {action.type}")
        print(f"Message Action value: {action.value}")
        print(f"Message Action timetoken: {action.message_timetoken}")
        print(f"Message Action uuid: {action.uuid}")
        print(f"Message Action timetoken: {action.action_timetoken}")
    # snippet.end

    built = envelope.result.actions
    a.eq(len(built) > 0 and built[-1].uuid, pubnub.uuid)

    # snippet.get_message_actions_named
    envelope = await pubnub.get_message_actions(channel="chats.room1", start=start, end=end, limit="50").future()
    # snippet.end
    named = envelope.result.actions
    limited = (await pubnub.get_message_actions(channel=channel, limit="2").future()).result.actions
    a.eq(len(limited), 2, 'limit caps the list')
    for token, action_timetoken in zip(tokens, (first, second, third)):
        await remove_action(pubnub, channel, token, action_timetoken)
    # Last on purpose: the SDK sends no end boundary when a start boundary is set (get_message_actions.py:50).
    a.eq([x.action_timetoken for x in built], [second], 'builder: start excluded, end included')
    a.eq(int(built[0].message_timetoken), tokens[1])
    a.eq([x.action_timetoken for x in named], [second], 'named arguments: same range')


@step('remove_message_action_builder', 'remove_message_action_named', role='open')
async def test_remove_message_action(aclients):
    pubnub = aclients.asyncio('open', 'remover')
    channel = names.with_suffix('chats.room1')
    seen = await alisten(aclients.asyncio('open', 'watcher'), channel)
    message_timetoken = (await publish_stored(pubnub, channel))[0]
    first = (await add_action(pubnub, channel, message_timetoken, 'smiley_face')).action_timetoken
    second = (await add_action(pubnub, channel, message_timetoken, 'thumbs_up')).action_timetoken
    await aeventually(lambda: a.eq(len(seen.message_actions), 2, 'added events received'))

    async def listed(expected):
        got = (await pubnub.get_message_actions(channel=channel).future()).result.actions
        a.eq([x.action_timetoken for x in got if int(x.message_timetoken) == message_timetoken], expected)

    await aeventually(lambda: listed([first, second]), timeout=30, what='both actions listed')
    action_timetoken = int(first)

    # snippet.remove_message_action_builder
    envelope = await pubnub.remove_message_action() \
        .channel("chats.room1") \
        .action_timetoken(action_timetoken) \
        .message_timetoken(message_timetoken) \
        .future()
    # snippet.end
    a.eq(envelope.status.is_error(), False)
    a.eq(envelope.result, {})
    await aeventually(lambda: listed([second]), timeout=30, what='first action removed')
    await aeventually(lambda: a.eq(len(seen.message_actions), 3, 'removed event received'))
    a.eq(seen.message_actions[2].action_timetoken, first)

    action_timetoken = int(second)
    # snippet.remove_message_action_named
    envelope = await pubnub.remove_message_action(channel="chats.room1",
                                                  action_timetoken=action_timetoken,
                                                  message_timetoken=message_timetoken) \
        .future()
    # snippet.end
    a.eq(envelope.result, {})
    await aeventually(lambda: listed([]), timeout=30, what='second action removed')
    await aeventually(lambda: a.eq(len(seen.message_actions), 4, 'second removed event received'))
    a.eq(seen.message_actions[3].action_timetoken, second)
    got = await pubnub.fetch_messages(channels=[channel], count=1, include_message_actions=True).future()
    a.eq(got.result.channels[channel][0].actions, {}, 'history shows no actions')
