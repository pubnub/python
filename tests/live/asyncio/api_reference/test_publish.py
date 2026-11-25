"""Docs page: publish (asyncio). Same steps as sync/publish.py with await."""
from support import assertions as a
from support import cleanup as live_cleanup
from support.listen import alisten
from support.wait import aeventually
from shared.publish import history_of, stored_has


async def test_publish_builder(aclients):
    """Snippets: publish_builder, publish_named."""
    pubnub = aclients.asyncio('open', 'publisher')
    channel = 'my_channel'
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
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
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
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
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


async def test_signal_message(aclients):
    """Snippet: signal_message."""
    pubnub = aclients.asyncio('open', 'signaler')
    channel = 'my_channel'
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.signal_message
    envelope = await pubnub.signal() \
        .channel("my_channel") \
        .message("typing_on") \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    await aeventually(lambda: a.eq([s.message for s in seen.signals], ['typing_on'], 'signals received'))
    a.eq(seen.messages, [], 'a signal is not a message')


async def test_fire_message(aclients):
    """Snippet: fire_message."""
    pubnub = aclients.asyncio('open', 'firer')
    channel = 'my_channel'
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.fire_message
    envelope = await pubnub.fire() \
        .channel("my_channel") \
        .message({'command': 'refresh'}) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    # A fired message is not replicated to subscribers. A normal publish after it proves the subscriber was listening.
    await pubnub.publish().channel(channel).message('after-fire').future()
    await aeventually(lambda: a.eq([m.message for m in seen.messages], ['after-fire'], 'only the later one arrived'))


async def test_publish_metadata(aclients):
    """Snippet: publish_metadata."""
    pubnub = aclients.asyncio('open', 'publisher')
    channel = 'my_channel'
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


async def test_publish_store_post(aclients):
    """Snippet: publish_store_post."""
    pubnub = aclients.asyncio('open', 'publisher')
    channel = 'my_channel'
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.publish_store_post
    stored = await pubnub.publish() \
        .channel("my_channel") \
        .message({'kept': True}) \
        .should_store(True) \
        .use_post(True) \
        .future()
    if stored.is_error():
        print(f"Error: {stored.status.error_data}")

    not_stored = await pubnub.publish() \
        .channel("my_channel") \
        .message({'kept': False}) \
        .should_store(False) \
        .use_post(True) \
        .future()
    if not_stored.is_error():
        print(f"Error: {not_stored.status.error_data}")
    # snippet.end

    a.timetoken(stored.result.timetoken)
    a.timetoken(not_stored.result.timetoken)
    await aeventually(lambda: a.eq(len(seen.messages), 2, 'both messages are delivered live'))
    a.eq(sorted(m.message['kept'] for m in seen.messages), [False, True], 'POST bodies arrive as JSON objects')

    await aeventually(lambda: stored_has(pubnub, channel, {'kept': True}))
    a.not_contains(await history_of(pubnub, channel), {'kept': False}, 'the should_store(False) message is not stored')
    live_cleanup.record('history', channel)
    refused = await pubnub.publish().channel(channel).message('x' * 33000).use_post(True).future()
    a.ok(refused.status.is_error(), 'POST publish of a message over 32 KiB is refused')
    a.eq(refused.status.status_code, 413, 'POST publish of a message over 32 KiB')
    small = await pubnub.publish().channel(channel).message('x' * 30000).use_post(True).future()
    a.timetoken(small.result.timetoken)


async def test_fire_post(aclients):
    """Snippet: fire_post."""
    pubnub = aclients.asyncio('open', 'firer')
    channel = 'my_channel'
    seen = await alisten(aclients.asyncio('open', 'subscriber'), channel)

    # snippet.fire_post
    envelope = await pubnub.fire().channel('my_channel').message('hello there').use_post(True).future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    else:
        print('fire timetoken: %d' % envelope.result.timetoken)
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    await pubnub.publish().channel(channel).message('after-fire-post').future()
    await aeventually(lambda: a.contains([m.message for m in seen.messages], 'after-fire-post', 'later publish'))
    a.not_contains([m.message for m in seen.messages], 'hello there', 'fired messages are not delivered')

    await aeventually(lambda: stored_has(pubnub, channel, 'after-fire-post'))
    a.not_contains(await history_of(pubnub, channel), 'hello there', 'fired messages are not stored in history')
    live_cleanup.record('history', channel)
