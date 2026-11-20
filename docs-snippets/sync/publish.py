"""Docs page: publish (sync). Template for the other pages.

The docs code sits between the snippet markers. Assertions and client setup sit outside them.
"""
from pubnub.exceptions import PubNubException

from harness import assertions as a
from harness import names
from harness import world
from harness.listeners import listen
from harness.step import step
from harness.wait import eventually


@step('publish_builder', 'publish_named', role='open')
def test_publish_message(clients):
    pubnub = clients.sync('open', 'publisher')
    channel = names.with_suffix('my_channel')
    seen = listen(clients.sync('open', 'subscriber'), channel)

    # snippet.publish_builder
    envelope = pubnub.publish() \
        .channel("my_channel") \
        .message({
            'name': 'Alex',
            'online': True
        }) \
        .custom_message_type("text-message") \
        .sync()
    # snippet.end
    first_timetoken = envelope.result.timetoken

    # snippet.publish_named
    envelope = pubnub.publish(
        channel="my_channel",
        message={
            'name': 'Sam',
            'online': False
        },
        custom_message_type="text-message",
        meta={'origin': 'docs'}
    ).sync()
    # snippet.end
    second_timetoken = envelope.result.timetoken

    a.timetoken(first_timetoken)
    a.timetoken(second_timetoken)
    eventually(lambda: a.eq(len(seen.messages), 2, 'messages received'))
    by_token = {m.timetoken: m for m in seen.messages}
    a.eq(by_token[first_timetoken].message, {'name': 'Alex', 'online': True})
    a.eq(by_token[first_timetoken].publisher, pubnub.uuid)
    a.eq(by_token[first_timetoken].custom_message_type, 'text-message')
    a.eq(by_token[second_timetoken].user_metadata, {'origin': 'docs'})


@step('signal_message', role='open')
def test_signal(clients):
    pubnub = clients.sync('open', 'signaler')
    channel = names.with_suffix('my_channel')
    seen = listen(clients.sync('open', 'subscriber'), channel)

    # snippet.signal_message
    envelope = pubnub.signal() \
        .channel("my_channel") \
        .message("typing_on") \
        .sync()
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    eventually(lambda: a.eq([s.message for s in seen.signals], ['typing_on'], 'signals received'))
    a.eq(seen.messages, [], 'a signal is not a message')


@step('fire_message', role='open')
def test_fire(clients):
    pubnub = clients.sync('open', 'firer')
    channel = names.with_suffix('my_channel')
    seen = listen(clients.sync('open', 'subscriber'), channel)

    # snippet.fire_message
    envelope = pubnub.fire() \
        .channel("my_channel") \
        .message({'command': 'refresh'}) \
        .sync()
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    # A fired message is not replicated to subscribers. A normal publish after it proves the subscriber was listening.
    pubnub.publish().channel(channel).message('after-fire').sync()
    eventually(lambda: a.eq([m.message for m in seen.messages], ['after-fire'], 'only the later publish arrived'))


@step('publish_metadata', role='open')
def test_publish_metadata(clients):
    pubnub = clients.sync('open', 'publisher')
    channel = names.with_suffix('my_channel')
    seen = listen(clients.sync('open', 'subscriber'), channel)
    outcomes = []

    # snippet.publish_metadata
    def publish_callback(result, status):
        # handle publish result, status always present, result if successful
        # status.is_error() to see if error happened
        # snippet.hide
        outcomes.append((result, status))
        # snippet.show
        if status.is_error():
            print(f"Publish failed: {status.error_data}")
        else:
            print(f"Publish timetoken: {result.timetoken}")

    pubnub.publish().channel("my_channel").message(["hello", "there"]) \
        .meta({'name': 'Alex'}).pn_async(publish_callback)
    # snippet.end

    eventually(lambda: a.eq(len(outcomes), 1, 'publish callback calls'))
    result, status = outcomes[0]
    a.ok(not status.is_error(), 'status is not an error')
    a.timetoken(result.timetoken)
    eventually(lambda: a.eq(len(seen.messages), 1, 'messages received'))
    a.eq(seen.messages[0].message, ['hello', 'there'])
    a.eq(seen.messages[0].user_metadata, {'name': 'Alex'})
    a.eq(seen.messages[0].timetoken, result.timetoken)


@step('publish_store_post', role='open')
def test_publish_store_and_post(clients):
    pubnub = clients.sync('open', 'publisher')
    channel = names.with_suffix('my_channel')
    seen = listen(clients.sync('open', 'subscriber'), channel)

    # snippet.publish_store_post
    stored = pubnub.publish() \
        .channel("my_channel") \
        .message({'kept': True}) \
        .should_store(True) \
        .use_post(True) \
        .sync()

    not_stored = pubnub.publish() \
        .channel("my_channel") \
        .message({'kept': False}) \
        .should_store(False) \
        .use_post(True) \
        .sync()
    # snippet.end

    a.timetoken(stored.result.timetoken)
    a.timetoken(not_stored.result.timetoken)
    eventually(lambda: a.eq(len(seen.messages), 2, 'both messages are delivered live'))
    a.eq(sorted(m.message['kept'] for m in seen.messages), [False, True], 'POST bodies arrive as JSON objects')

    def history_messages():
        items = pubnub.fetch_messages(channels=[channel]).sync().result.channels.get(channel, [])
        return [item.message for item in items]

    eventually(lambda: a.contains(history_messages(), {'kept': True}, 'the should_store(True) message is stored'))
    a.not_contains(history_messages(), {'kept': False}, 'the should_store(False) message is not stored')
    world.record('history', channel)
    error = a.raises(PubNubException,
                     lambda: pubnub.publish().channel(channel).message('x' * 33000).use_post(True).sync())
    # The docs promise a "Message Too Large" error, the service answers 413 Request Entity Too Large
    a.contains(str(error), '413', 'POST publish of a message over 32 KiB')
    small = pubnub.publish().channel(channel).message('x' * 30000).use_post(True).sync()
    a.timetoken(small.result.timetoken)
    # Over GET the same payload never reaches the size check, the balancer answers 414 first
    uri_error = a.raises(PubNubException, lambda: pubnub.publish().channel(channel).message('x' * 40000).sync())
    a.contains(str(uri_error), '414', 'GET publish of an oversize message')


@step('fire_post', 'fire_named', role='open')
def test_fire_post_and_named(clients):
    pubnub = clients.sync('open', 'firer')
    channel = names.with_suffix('my_channel')
    seen = listen(clients.sync('open', 'subscriber'), channel)

    # snippet.fire_post
    envelope = pubnub.fire() \
        .channel('my_channel') \
        .message('hello there') \
        .use_post(True) \
        .sync()
    print(f'fire timetoken: {envelope.result.timetoken}')
    # snippet.end
    first = envelope.result.timetoken

    # snippet.fire_named
    fire = pubnub.fire(channel="my_channel", message='hello there').sync()
    print(f'fire timetoken: {fire.result.timetoken}')
    # snippet.end

    a.timetoken(first)
    a.timetoken(fire.result.timetoken)
    pubnub.publish().channel(channel).message('after-fire-post').sync()
    eventually(lambda: a.contains([m.message for m in seen.messages], 'after-fire-post', 'the later publish arrived'))
    a.not_contains([m.message for m in seen.messages], 'hello there', 'fired messages are not delivered')

    def history_messages():
        items = pubnub.fetch_messages(channels=[channel]).sync().result.channels.get(channel, [])
        return [item.message for item in items]

    eventually(lambda: a.contains(history_messages(), 'after-fire-post', 'the later publish is stored'))
    a.not_contains(history_messages(), 'hello there', 'fired messages are not stored in history')
    world.record('history', channel)


@step('signal_named', role='open')
def test_signal_named(clients):
    pubnub = clients.sync('open', 'signaler')
    channel = names.with_suffix('my_channel')
    seen = listen(clients.sync('open', 'subscriber'), channel)

    # snippet.signal_named
    signal = pubnub.signal(channel="my_channel", message='hello there', custom_message_type='text-message').sync()
    print(f'signal timetoken: {signal.result.timetoken}')
    # snippet.end

    a.timetoken(signal.result.timetoken)
    eventually(lambda: a.eq(len(seen.signals), 1, 'signals received'))
    a.eq(seen.signals[0].message, 'hello there')
    a.eq(seen.signals[0].custom_message_type, 'text-message')
    a.eq(seen.signals[0].publisher, pubnub.uuid)
    too_big = a.raises(PubNubException, lambda: pubnub.signal(channel=channel, message='s' * 100).sync())
    a.ok(too_big is not None, 'the docs promise a 64 byte signal payload limit')
