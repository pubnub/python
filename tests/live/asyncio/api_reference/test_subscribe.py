"""Docs page: subscribe (asyncio). Subscribe, Entities, Event listeners, Unsubscribe and the old-style methods."""
from pubnub.enums import PNStatusCategory
from pubnub.models.server.subscribe import SubscribeMessage
from pubnub.models.consumer.message_actions import PNMessageAction

from support import assertions as a
from support import cleanup as live_cleanup
from support.listen import alisten
from support.wait import PRESENCE_EVENT_TIMEOUT, aeventually
from shared.presence import not_present
from shared.subscribe import AppContextCollector, Printed, attach, connected_async as connected, texts


async def test_subscribe_single(aclients):
    """Snippet: subscribe_single."""
    pubnub = aclients.asyncio('open', 'subscriber')
    publisher = aclients.asyncio('open', 'publisher')
    name = 'my_channel'
    seen = attach(pubnub)

    # snippet.subscribe_single
    # single channel subscription
    channel = pubnub.channel("my_channel")
    t1_subscription = channel.subscription()
    t1_subscription.subscribe()
    # snippet.end

    a.eq(channel.name, name)
    await connected(seen)
    await publisher.publish().channel(name).message('hello single').future()
    await aeventually(lambda: a.eq(texts(seen), ['hello single'], 'messages received'))
    a.eq(seen.messages[0].channel, name)


async def test_subscribe_multiple(aclients):
    """Snippet: subscribe_multiple."""
    pubnub = aclients.asyncio('open', 'subscriber')
    publisher = aclients.asyncio('open', 'publisher')
    name = 'my_channel'
    group_name = 'group-test'
    grouped = 'grouped_channel'
    await publisher.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).future()
    live_cleanup.record('channel_group', group_name)
    # The join of second_user is checked below. The service emits it only if the user ID is not an occupant yet.
    not_present(f'{name}.2', ['second_user'])
    seen = attach(pubnub)
    envelopes = []
    original_from_json = SubscribeMessage.from_json.__func__

    def counting_from_json(cls, json_input):
        if json_input.get('d') == 'second':
            envelopes.append(json_input['c'])
        return original_from_json(cls, json_input)

    SubscribeMessage.from_json = classmethod(counting_from_json)
    try:
        # snippet.subscribe_multiple
        channel = "my_channel"

        # multiple channel subscription
        channel_1 = pubnub.channel(channel).subscription()
        channel_2 = pubnub.channel(f'{channel}.2').subscription(with_presence=True)
        channel_x = pubnub.channel(f'{channel}.*').subscription(with_presence=True)

        group = pubnub.channel_group("group-test").subscription()

        subscription_set = pubnub.subscription_set([channel_1, channel_2, channel_x, group])

        subscription_set.subscribe()
        # snippet.end

        await connected(seen)
        await publisher.publish().channel(name).message('plain').future()
        await publisher.publish().channel(f'{name}.2').message('second').future()
        await publisher.publish().channel(f'{name}.other').message('wildcard').future()
        await publisher.publish().channel(grouped).message('group').future()
        # The message on 'my_channel.2' matches two subscriptions: the channel itself and the wildcard
        # 'my_channel.*'. The service sends one envelope per matching subscription, and for the same request the
        # asyncio client got one or two of them, run to run (sync got two in every run). The SDK delivers every
        # envelope it receives (pubnub/event_engine/effects.py:142 passes the whole 'm' list on, pubnub/workers.py:215
        # announces each one). The proof: copies at the listener equal envelopes received, and never more than
        # the number of matching subscriptions.
        matching = {f'{name}.2', f'{name}.*'}
        await aeventually(lambda: a.eq(sorted(set(texts(seen))), ['group', 'plain', 'second', 'wildcard'],
                                       'distinct messages'))
        await aeventually(lambda: a.eq({text: texts(seen).count(text) for text in set(texts(seen))
                                        if text != 'second'}, {'plain': 1, 'wildcard': 1, 'group': 1},
                                       'messages with one matching subscription arrive once'))
        await aeventually(lambda: a.eq(texts(seen).count('second'), envelopes.count(f'{name}.2'),
                                       'one delivery per envelope the SDK received'))
        a.ok(1 <= envelopes.count(f'{name}.2') <= len(matching), 'at most one envelope per matching subscription')
        second = [m for m in seen.messages if m.message == 'second']
        a.eq({m.timetoken for m in second}, {second[0].timetoken}, 'the copies are the same published message')
        by_text = {m.message: m for m in seen.messages}
        a.eq(by_text['plain'].channel, name)
        a.eq(by_text['wildcard'].channel, f'{name}.other')
        a.eq(by_text['wildcard'].subscription, f'{name}.*', 'wildcard match is reported as subscription')
        a.eq(by_text['group'].channel, grouped)
        a.eq(by_text['group'].subscription, group_name, 'channel group match is reported as subscription')

        other = aclients.asyncio('open', 'second_user')
        await alisten(other, f'{name}.2')
        await aeventually(lambda: a.contains([(p.event, p.uuid) for p in seen.presence_events
                                              if p.channel == f'{name}.2'],
                                             ('join', other.uuid), 'join of the second client'),
                          timeout=PRESENCE_EVENT_TIMEOUT)
    finally:
        SubscribeMessage.from_json = classmethod(original_from_json)


async def test_entity_channel(aclients):
    """Snippets: entity_channel, entity_channel_group, entity_channel_metadata, entity_user_metadata."""
    pubnub = aclients.asyncio('open', 'subscriber')
    other = aclients.asyncio('open', 'publisher')
    name = 'my_channel'
    group_name = 'channelGroupName'
    meta_name = 'channelMetadata'
    user_name = 'user_metadata'
    grouped = 'grouped_channel'
    seen = AppContextCollector()
    pubnub.subscribed_by_suite = True
    pubnub.add_listener(seen)

    # snippet.entity_channel
    channel = pubnub.channel("my_channel")
    # snippet.end

    # snippet.entity_channel_group
    channel_group = pubnub.channel_group("channelGroupName")
    # snippet.end

    # snippet.entity_channel_metadata
    channel_metadata = pubnub.channel_metadata("channelMetadata")
    # snippet.end

    # snippet.entity_user_metadata
    user_metadata = pubnub.user_metadata("user_metadata")
    # snippet.end

    a.eq((type(channel).__name__, channel.name), ('PubNubChannel', name))
    a.eq((type(channel_group).__name__, channel_group.name), ('PubNubChannelGroup', group_name))
    a.eq((type(channel_metadata).__name__, channel_metadata.name), ('PubNubChannelMetadata', meta_name))
    a.eq((type(user_metadata).__name__, user_metadata.name), ('PubNubUserMetadata', user_name))

    await other.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).future()
    live_cleanup.record('channel_group', group_name)
    # SDK bug: PubNubUserMetadata sets _types instead of _type, so its subscription would register the user ID as a
    # channel group. Delivery for user metadata is therefore not exercised here, see the report.
    pubnub.subscription_set([channel.subscription(), channel_group.subscription(),
                             channel_metadata.subscription()]).subscribe()
    await connected(seen)
    try:
        await other.publish().channel(name).message('on the channel').future()
        await other.publish().channel(grouped).message('through the group').future()
        await other.set_channel_metadata().channel(meta_name).set_name('Entity channel').future()
        await aeventually(
            lambda: a.eq(sorted(texts(seen)), ['on the channel', 'through the group'], 'messages received'))
        await aeventually(
            lambda: a.eq([e.data['id'] for e in seen.channel_events], [meta_name], 'channel metadata event'))
    finally:
        await other.remove_channel_metadata().channel(meta_name).future()


async def test_listeners_event_specific(aclients, capsys):
    """Snippet: listeners_event_specific."""
    pubnub = aclients.asyncio('open', 'subscriber')
    publisher = aclients.asyncio('open', 'publisher')
    name = 'my_channel'
    seen = attach(pubnub)
    printed = Printed(capsys)

    # snippet.listeners_event_specific
    subscription = pubnub.channel("my_channel").subscription()

    # using closure for reusable listener
    def on_message(listener):
        def message_callback(message):
            print(f"\033[94mMessage received on: {listener}: \n{message.message}\033[0m\n")
        return message_callback

    # without closure
    def on_message_action(message_action):
        print(f"\033[5mMessageAction received: \n{message_action.value}\033[0m\n")

    def on_signal(listener):
        def signal_callback(signal):
            print(f"\033[0;36mSignal received on: {listener}: \n{signal.publisher} says: \t{signal.message}\033[0m")
        return signal_callback

    subscription.on_message = on_message('message_listener')
    subscription.on_message_action = on_message_action
    subscription.on_signal = on_signal('signal_listener')

    subscription.subscribe()
    # snippet.end

    await connected(seen)
    envelope = await publisher.publish().channel(name).message('listener message').future()
    await publisher.signal().channel(name).message('listener signal').future()
    action = PNMessageAction().create(type='reaction', value='smile', message_timetoken=envelope.result.timetoken)
    await publisher.add_message_action().channel(name).message_action(action).future()
    await aeventually(
        lambda: a.contains(printed.text(), 'Message received on: message_listener: \n', 'message printed'))
    await aeventually(lambda: a.contains(printed.text(), 'listener message', 'message payload printed'))
    await aeventually(lambda: a.contains(printed.text(), f'{publisher.uuid} says: \tlistener signal', 'signal printed'))
    await aeventually(lambda: a.contains(printed.text(), 'MessageAction received: \nsmile', 'message action printed'))


async def test_listeners_generic(aclients, capsys):
    """Snippet: listeners_generic."""
    pubnub = aclients.asyncio('open', 'subscriber')
    publisher = aclients.asyncio('open', 'publisher')
    name = 'my_channel'
    seen = attach(pubnub)
    printed = Printed(capsys)

    # snippet.listeners_generic
    from pubnub.callbacks import SubscribeCallback

    # add generic listener
    class PrintListener(SubscribeCallback):
        def status(self, _, status):
            print(f'\033[92mPrintListener.status:\n{status.category.name}\033[0m')

        def message(self, _, message):
            print(f'\033[94mPrintListener.message:\n{message.message}\033[0m')

        def presence(self, _, presence):
            print(f'PrintListener.presence:\n{presence.uuid} {presence.event}s '
                  f'{presence.subscription or presence.channel}\033[0m')

        def signal(self, _, signal):
            print(f'PrintListener.signal:\n{signal.message} from {signal.publisher}\033[0m')

        def channel(self, _, channel):
            print(f'\033[0;37mChannel Meta:\n{channel.__dict__}\033[0m')

        def uuid(self, _, uuid):
            print(f'User Meta:\n{uuid.__dict__}\033[0m')

        def membership(self, _, membership):
            print(f'Membership:\n{membership.__dict__}\033[0m')

        def message_action(self, _, message_action):
            print(f'PrintListener.message_action {message_action}\033[0m')

        def file(self, _, file_message):
            print(f' {file_message.__dict__}\033[0m')

    # The docs call subscription.add_listener(PrintListener()). The SDK then calls PrintListener.message(message)
    # without the pubnub argument and raises TypeError, so the client-level add_listener is used here.
    pubnub.add_listener(PrintListener())

    subscription = pubnub.channel("my_channel").subscription()
    subscription.subscribe()
    # snippet.end

    await connected(seen)
    await publisher.publish().channel(name).message('generic message').future()
    await publisher.signal().channel(name).message('generic signal').future()
    await aeventually(lambda: a.contains(printed.text(), 'PrintListener.message:\ngeneric message', 'message printed'))
    await aeventually(lambda: a.contains(printed.text(), f'PrintListener.signal:\ngeneric signal from {publisher.uuid}',
                                         'signal printed'))


async def test_listeners_subscription_set(aclients, capsys):
    """Snippet: listeners_subscription_set."""
    pubnub = aclients.asyncio('open', 'subscriber')
    publisher = aclients.asyncio('open', 'publisher')
    names_in_set = ['my_channel', 'my_channel_2']
    group_name = 'cg_1'
    grouped = 'grouped_channel'
    await publisher.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).future()
    live_cleanup.record('channel_group', group_name)
    seen = attach(pubnub)
    printed = Printed(capsys)

    # snippet.listeners_subscription_set
    def on_message(listener):
        def message_callback(message):
            print(f"\033[94mMessage received on: {listener}: \n{message.message}\033[0m\n")
        return message_callback

    subscription_set = pubnub.subscription_set([
        pubnub.channel("my_channel").subscription(),
        pubnub.channel("my_channel_2").subscription(),
        pubnub.channel_group("cg_1").subscription()
    ])
    subscription_set.on_message = on_message('set_listener')

    subscription_set.subscribe()
    # snippet.end

    await connected(seen)
    for target, text in zip(names_in_set + [grouped], ['first', 'second', 'third']):
        await publisher.publish().channel(target).message(text).future()
    for text in ['first', 'second', 'third']:
        await aeventually(lambda: a.contains(printed.text(), f'Message received on: set_listener: \n{text}\x1b', text))


async def test_listeners_presence(aclients, capsys):
    """Snippet: listeners_presence."""
    pubnub = aclients.asyncio('open', 'subscriber')
    name = 'my_channel'
    seen = attach(pubnub)
    printed = Printed(capsys)

    # snippet.listeners_presence
    def on_presence(listener):
        def presence_callback(presence):
            print(f"\033[0;32mPresence received on: {listener}: \t{presence.uuid} {presence.event}s "
                  f"{presence.subscription or presence.channel}\033[0m")
        return presence_callback

    subscription = pubnub.channel("my_channel").subscription(with_presence=True)
    subscription.on_presence = on_presence('presence_listener')

    subscription.subscribe()
    # snippet.end

    await connected(seen)
    other = aclients.asyncio('open', 'second_user')
    await alisten(other, name)
    await aeventually(
        lambda: a.contains(printed.text(), f'presence_listener: \t{other.uuid} joins {name}', 'join printed'))


async def test_listeners_status(aclients, capsys):
    """Snippet: listeners_status."""
    pubnub = aclients.asyncio('open', 'subscriber')
    printed = Printed(capsys)

    # snippet.listeners_status
    from pubnub.pubnub_asyncio import SubscribeListener

    class PrintListener(SubscribeListener):
        def status(self, pubnub, status):
            print(f'Status:\n{status.__dict__}')

        def message(self, pubnub, message):
            pass

        def presence(self, pubnub, presence):
            pass

    listener = PrintListener()
    pubnub.add_listener(listener)
    # snippet.end

    pubnub.subscribed_by_suite = True
    pubnub.channel("my_channel").subscription().subscribe()
    await aeventually(lambda: a.contains(printed.text(), 'PNConnectedCategory', 'connected status printed'))
    a.contains(printed.text(), 'Status:\n{', 'status dictionary printed')


async def test_unsubscribe_subscription(aclients):
    """Snippet: unsubscribe_subscription."""
    pubnub = aclients.asyncio('open', 'subscriber')
    publisher = aclients.asyncio('open', 'publisher')
    single, control = 'my_channel', 'ch3'
    seen = attach(pubnub)
    pubnub.channel(control).subscription().subscribe()

    t1_subscription = pubnub.channel(single).subscription()
    t1_subscription.subscribe()
    await connected(seen)
    await publisher.publish().channel(single).message('before').future()
    await aeventually(lambda: a.eq(texts(seen), ['before'], 'message before unsubscribe'))

    # snippet.unsubscribe_subscription
    t1_subscription.unsubscribe()
    # snippet.end

    await aeventually(lambda: a.eq(pubnub.get_subscribed_channels(), [control], 'channels left'))
    await publisher.publish().channel(single).message('after single').future()
    await publisher.publish().channel(control).message('after control').future()
    await aeventually(lambda: a.contains(texts(seen), 'after control', 'the control channel still delivers'))
    a.not_contains(texts(seen), 'after single', 'no message after unsubscribe')


async def test_unsubscribe_set(aclients):
    """Snippet: unsubscribe_set."""
    pubnub = aclients.asyncio('open', 'subscriber')
    publisher = aclients.asyncio('open', 'publisher')
    first, second, control = [n for n in ('ch1', 'ch2', 'ch3')]
    seen = attach(pubnub)
    pubnub.channel(control).subscription().subscribe()

    subscription_set = pubnub.subscription_set([
        pubnub.channel(first).subscription(),
        pubnub.channel(second).subscription()
    ])
    subscription_set.subscribe()
    await connected(seen)
    await publisher.publish().channel(first).message('before first').future()
    await publisher.publish().channel(second).message('before second').future()
    await aeventually(
        lambda: a.eq(sorted(texts(seen)), ['before first', 'before second'], 'messages before unsubscribe'))

    # snippet.unsubscribe_set
    subscription_set.unsubscribe()
    # snippet.end

    await aeventually(lambda: a.eq(pubnub.get_subscribed_channels(), [control], 'channels left'))
    await publisher.publish().channel(first).message('after first').future()
    await publisher.publish().channel(second).message('after second').future()
    await publisher.publish().channel(control).message('after control').future()
    await aeventually(lambda: a.contains(texts(seen), 'after control', 'the control channel still delivers'))
    a.not_contains(texts(seen), 'after first', 'no message after unsubscribe')
    a.not_contains(texts(seen), 'after second', 'no message after unsubscribe')


async def test_unsubscribe_all(aclients):
    """Snippet: unsubscribe_all."""
    pubnub = aclients.asyncio('open', 'subscriber')
    publisher = aclients.asyncio('open', 'publisher')
    single, first = [n for n in ('my_channel', 'ch1')]
    seen = attach(pubnub)
    pubnub.channel(single).subscription().subscribe()
    pubnub.subscription_set([pubnub.channel(first).subscription()]).subscribe()
    await connected(seen)
    a.eq(sorted(pubnub.get_subscribed_channels()), sorted([single, first]))

    # snippet.unsubscribe_all
    pubnub.unsubscribe_all()
    # snippet.end

    # unsubscribe_all() leaves the registry unusable (see the report), so the harness must not call it again
    pubnub.subscribed_by_suite = False
    await aeventually(lambda: a.eq(pubnub.get_subscribed_channels(), [], 'channels left'))
    await aeventually(
        lambda: a.contains(seen.categories, PNStatusCategory.PNAcknowledgmentCategory, 'leave acknowledged'))
    await publisher.publish().channel(single).message('after single').future()
    await publisher.publish().channel(first).message('after first').future()
    a.eq(texts(seen), [], 'no message after unsubscribe_all')
