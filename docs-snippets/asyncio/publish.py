"""Docs page: publish (asyncio). Same steps as sync/publish.py with await."""
from harness import assertions as a
from harness import names
from harness import world
from harness.listeners import alisten
from harness.step import step
from harness.wait import aeventually


@step('publish_builder', 'publish_named', role='open')
async def test_publish_message(aclients):
    pubnub = aclients.asyncio('open', 'publisher')
    channel = names.with_suffix('my_channel')
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.publish_builder
    envelope = await pubnub.publish() \
        .channel("my_channel") \
        .message({
            'name': 'Alex',
            'online': True
        }) \
        .custom_message_type("text-message") \
        .future()
    # snippet.end
    first_timetoken = envelope.result.timetoken

    # snippet.publish_named
    envelope = await pubnub.publish(
        channel="my_channel",
        message={
            'name': 'Sam',
            'online': False
        },
        custom_message_type="text-message",
        meta={'origin': 'docs'}
    ).future()
    # snippet.end
    second_timetoken = envelope.result.timetoken

    a.timetoken(first_timetoken)
    a.timetoken(second_timetoken)
    await aeventually(lambda: a.eq(len(seen.messages), 2, 'messages received'))
    by_token = {m.timetoken: m for m in seen.messages}
    a.eq(by_token[first_timetoken].message, {'name': 'Alex', 'online': True})
    a.eq(by_token[first_timetoken].publisher, pubnub.uuid)
    a.eq(by_token[first_timetoken].custom_message_type, 'text-message')
    a.eq(by_token[second_timetoken].user_metadata, {'origin': 'docs'})


@step('signal_message', role='open')
async def test_signal(aclients):
    pubnub = aclients.asyncio('open', 'signaler')
    channel = names.with_suffix('my_channel')
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.signal_message
    envelope = await pubnub.signal() \
        .channel("my_channel") \
        .message("typing_on") \
        .future()
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    await aeventually(lambda: a.eq([s.message for s in seen.signals], ['typing_on'], 'signals received'))
    a.eq(seen.messages, [], 'a signal is not a message')


@step('fire_message', role='open')
async def test_fire(aclients):
    pubnub = aclients.asyncio('open', 'firer')
    channel = names.with_suffix('my_channel')
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.fire_message
    envelope = await pubnub.fire() \
        .channel("my_channel") \
        .message({'command': 'refresh'}) \
        .future()
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    # A fired message is not replicated to subscribers. A normal publish after it proves the subscriber was listening.
    await pubnub.publish().channel(channel).message('after-fire').future()
    await aeventually(lambda: a.eq([m.message for m in seen.messages], ['after-fire'], 'only the later one arrived'))


async def history_of(pubnub, channel):
    fetched = await pubnub.fetch_messages(channels=[channel]).future()
    return [item.message for item in fetched.result.channels.get(channel, [])]


async def stored_has(pubnub, channel, wanted):
    a.contains(await history_of(pubnub, channel), wanted, 'message is stored in history')


@step('publish_metadata', role='open')
async def test_publish_metadata(aclients):
    pubnub = aclients.asyncio('open', 'publisher')
    channel = names.with_suffix('my_channel')
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.publish_metadata
    envelope = await pubnub.publish()\
        .channel("my_channel")\
        .message(["hello", "there"])\
        .meta({'name': 'Alex'})\
        .future()
    # handle publish result, status always present, result if successful
    # envelope.status.is_error() to see if error happened
    # snippet.end

    a.ok(not envelope.status.is_error(), 'status is not an error')
    a.timetoken(envelope.result.timetoken)
    await aeventually(lambda: a.eq(len(seen.messages), 1, 'messages received'))
    a.eq(seen.messages[0].message, ['hello', 'there'])
    a.eq(seen.messages[0].user_metadata, {'name': 'Alex'})
    a.eq(seen.messages[0].timetoken, envelope.result.timetoken)


@step('publish_store_post', role='open')
async def test_publish_store_and_post(aclients):
    pubnub = aclients.asyncio('open', 'publisher')
    channel = names.with_suffix('my_channel')
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.publish_store_post
    stored = await pubnub.publish() \
        .channel("my_channel") \
        .message({'kept': True}) \
        .should_store(True) \
        .use_post(True) \
        .future()

    not_stored = await pubnub.publish() \
        .channel("my_channel") \
        .message({'kept': False}) \
        .should_store(False) \
        .use_post(True) \
        .future()
    # snippet.end

    a.timetoken(stored.result.timetoken)
    a.timetoken(not_stored.result.timetoken)
    await aeventually(lambda: a.eq(len(seen.messages), 2, 'both messages are delivered live'))
    a.eq(sorted(m.message['kept'] for m in seen.messages), [False, True], 'POST bodies arrive as JSON objects')

    await aeventually(lambda: stored_has(pubnub, channel, {'kept': True}))
    a.not_contains(await history_of(pubnub, channel), {'kept': False}, 'the should_store(False) message is not stored')
    world.record('history', channel)
    refused = await pubnub.publish().channel(channel).message('x' * 33000).use_post(True).future()
    a.ok(refused.status.is_error(), 'POST publish of a message over 32 KiB is refused')
    a.eq(refused.status.status_code, 413, 'POST publish of a message over 32 KiB')
    small = await pubnub.publish().channel(channel).message('x' * 30000).use_post(True).future()
    a.timetoken(small.result.timetoken)


@step('fire_post', role='open')
async def test_fire_post(aclients):
    pubnub = aclients.asyncio('open', 'firer')
    channel = names.with_suffix('my_channel')
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.fire_post
    envelope = await pubnub.fire().channel('my_channel').message('hello there').use_post(True).future()
    print('fire timetoken: %d' % envelope.result.timetoken)
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    await pubnub.publish().channel(channel).message('after-fire-post').future()
    await aeventually(lambda: a.contains([m.message for m in seen.messages], 'after-fire-post', 'later publish'))
    a.not_contains([m.message for m in seen.messages], 'hello there', 'fired messages are not delivered')

    await aeventually(lambda: stored_has(pubnub, channel, 'after-fire-post'))
    a.not_contains(await history_of(pubnub, channel), 'hello there', 'fired messages are not stored in history')
    world.record('history', channel)
