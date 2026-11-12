"""Docs page: subscribe (sync). Subscribe, Entities, Event listeners, Unsubscribe and the old-style methods."""
from pubnub.enums import PNStatusCategory
from pubnub.models.server.subscribe import SubscribeMessage

from harness import assertions as a
from harness import names
from harness import world
from harness.listeners import Collector, listen
from harness.step import compile_only, step
from harness.wait import eventually
from pubnub.models.consumer.message_actions import PNMessageAction

REGISTERED_NAMES = ['group-test', 'channelGroupName', 'channelMetadata', 'user_metadata', 'cg_1',
                    'awesome_channel_group', 'my_channel1', 'my_channel2', 'my_group1', 'my_group2']


def attach(client):
    """Add a collector to a client without subscribing. The docs code does the subscribing."""
    collector = Collector()
    client.subscribed_by_suite = True
    client.add_listener(collector)
    return collector


def connected(collector):
    eventually(lambda: a.ok(PNStatusCategory.PNConnectedCategory in collector.categories, 'not connected yet'),
               what='PNConnectedCategory')


def texts(collector):
    return [m.message for m in collector.messages]


@step('subscribe_single', role='open')
def test_subscribe_single(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = names.with_suffix('my_channel')
    seen = attach(pubnub)

    # snippet.subscribe_single
    # single channel subscription
    channel = pubnub.channel("my_channel")
    t1_subscription = channel.subscription()
    t1_subscription.subscribe()
    # snippet.end

    a.eq(channel.name, name)
    connected(seen)
    publisher.publish().channel(name).message('hello single').sync()
    eventually(lambda: a.eq(texts(seen), ['hello single'], 'messages received'))
    a.eq(seen.messages[0].channel, name)


@step('subscribe_multiple', role='open')
def test_subscribe_multiple(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = names.with_suffix('my_channel')
    group_name = names.with_suffix('group-test')
    grouped = names.with_suffix('grouped_channel')
    publisher.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).sync()
    world.record('channel_group', group_name)
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

        connected(seen)
        publisher.publish().channel(name).message('plain').sync()
        publisher.publish().channel(f'{name}.2').message('second').sync()
        publisher.publish().channel(f'{name}.other').message('wildcard').sync()
        publisher.publish().channel(grouped).message('group').sync()
        # The message on 'my_channel.2' matches two subscriptions: the channel itself and the wildcard
        # 'my_channel.*'. The service sends one envelope per matching subscription, and for the same request the sync
        # client got one or two of them, run to run. The SDK delivers every envelope it receives
        # (pubnub/managers.py:373-374 loops over all of them, pubnub/workers.py:215 announces each one). The proof:
        # copies at the listener equal envelopes received, and never more than the number of matching subscriptions.
        matching = {f'{name}.2', f'{name}.*'}
        eventually(lambda: a.eq(sorted(set(texts(seen))), ['group', 'plain', 'second', 'wildcard'],
                                'distinct messages'))
        eventually(lambda: a.eq({text: texts(seen).count(text) for text in set(texts(seen)) if text != 'second'},
                                {'plain': 1, 'wildcard': 1, 'group': 1},
                                'messages with one matching subscription arrive once'))
        eventually(lambda: a.eq(texts(seen).count('second'), envelopes.count(f'{name}.2'),
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

        other = clients.sync('open', 'second_user')
        listen(other, f'{name}.2')
        eventually(lambda: a.contains([(p.event, p.uuid) for p in seen.presence_events if p.channel == f'{name}.2'],
                                      ('join', other.uuid), 'join of the second client'))
    finally:
        SubscribeMessage.from_json = classmethod(original_from_json)


class AppContextCollector(Collector):
    """Collector that also keeps App Context events."""

    def __init__(self):
        super().__init__()
        self.channel_events = []
        self.uuid_events = []

    def channel(self, pubnub, channel):
        with self._lock:
            self.channel_events.append(channel)

    def uuid(self, pubnub, uuid):
        with self._lock:
            self.uuid_events.append(uuid)


@step('entity_channel', 'entity_channel_group', 'entity_channel_metadata', 'entity_user_metadata', role='open')
def test_entities(clients):
    pubnub = clients.sync('open', 'subscriber')
    other = clients.sync('open', 'publisher')
    name = names.with_suffix('my_channel')
    group_name = names.with_suffix('channelGroupName')
    meta_name = names.with_suffix('channelMetadata')
    user_name = names.with_suffix('user_metadata')
    grouped = names.with_suffix('grouped_channel')
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

    other.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).sync()
    world.record('channel_group', group_name)
    # SDK bug: PubNubUserMetadata sets _types instead of _type, so its subscription would register the user ID as a
    # channel group. Delivery for user metadata is therefore not exercised here, see the report.
    pubnub.subscription_set([channel.subscription(), channel_group.subscription(),
                             channel_metadata.subscription()]).subscribe()
    connected(seen)
    try:
        other.publish().channel(name).message('on the channel').sync()
        other.publish().channel(grouped).message('through the group').sync()
        other.set_channel_metadata().channel(meta_name).set_name('Entity channel').sync()
        eventually(lambda: a.eq(sorted(texts(seen)), ['on the channel', 'through the group'], 'messages received'))
        eventually(lambda: a.eq([e.data['id'] for e in seen.channel_events], [meta_name], 'channel metadata event'))
    finally:
        other.remove_channel_metadata().channel(meta_name).sync()


class Printed:
    """Everything the docs listeners printed so far. Callbacks run on SDK threads, capsys sees their output."""

    def __init__(self, capsys):
        self._capsys = capsys
        self._parts = []

    def text(self):
        self._parts.append(self._capsys.readouterr().out)
        return ''.join(self._parts)


@step('listeners_event_specific', role='open')
def test_listeners_event_specific(clients, capsys):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = names.with_suffix('my_channel')
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

    connected(seen)
    envelope = publisher.publish().channel(name).message('listener message').sync()
    publisher.signal().channel(name).message('listener signal').sync()
    action = PNMessageAction().create(type='reaction', value='smile', message_timetoken=envelope.result.timetoken)
    publisher.add_message_action().channel(name).message_action(action).sync()
    eventually(lambda: a.contains(printed.text(), 'Message received on: message_listener: \n', 'message printed'))
    eventually(lambda: a.contains(printed.text(), 'listener message', 'message payload printed'))
    eventually(lambda: a.contains(printed.text(), f'{publisher.uuid} says: \tlistener signal', 'signal printed'))
    eventually(lambda: a.contains(printed.text(), 'MessageAction received: \nsmile', 'message action printed'))


@step('listeners_generic', role='open')
def test_listeners_generic(clients, capsys):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = names.with_suffix('my_channel')
    seen = attach(pubnub)
    printed = Printed(capsys)

    # snippet.listeners_generic
    # snippet.hide
    from pubnub.callbacks import SubscribeCallback
    # snippet.show

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

    connected(seen)
    publisher.publish().channel(name).message('generic message').sync()
    publisher.signal().channel(name).message('generic signal').sync()
    eventually(lambda: a.contains(printed.text(), 'PrintListener.message:\ngeneric message', 'message printed'))
    eventually(lambda: a.contains(printed.text(), f'PrintListener.signal:\ngeneric signal from {publisher.uuid}',
                                  'signal printed'))


@step('listeners_subscription_set', role='open')
def test_listeners_subscription_set(clients, capsys):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    names_in_set = [names.with_suffix('my_channel'), names.with_suffix('my_channel_2')]
    group_name = names.with_suffix('cg_1')
    grouped = names.with_suffix('grouped_channel')
    publisher.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).sync()
    world.record('channel_group', group_name)
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

    connected(seen)
    for target, text in zip(names_in_set + [grouped], ['first', 'second', 'third']):
        publisher.publish().channel(target).message(text).sync()
    for text in ['first', 'second', 'third']:
        eventually(lambda: a.contains(printed.text(), f'Message received on: set_listener: \n{text}\x1b', text))


@step('listeners_presence', role='open')
def test_listeners_presence(clients, capsys):
    pubnub = clients.sync('open', 'subscriber')
    name = names.with_suffix('my_channel')
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

    connected(seen)
    other = clients.sync('open', 'second_user')
    listen(other, name)
    eventually(lambda: a.contains(printed.text(), f'presence_listener: \t{other.uuid} joins {name}', 'join printed'))


@step('listeners_status', role='open')
def test_listeners_status(clients, capsys):
    pubnub = clients.sync('open', 'subscriber')
    printed = Printed(capsys)

    # snippet.listeners_status
    # snippet.hide
    from pubnub.pubnub import SubscribeListener
    # snippet.show

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
    eventually(lambda: a.contains(printed.text(), 'PNConnectedCategory', 'connected status printed'))
    a.contains(printed.text(), 'Status:\n{', 'status dictionary printed')


@step('unsubscribe_subscription', role='open')
def test_unsubscribe_subscription(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    single, control = names.with_suffix('my_channel'), names.with_suffix('ch3')
    seen = attach(pubnub)
    pubnub.channel(control).subscription().subscribe()

    t1_subscription = pubnub.channel(single).subscription()
    t1_subscription.subscribe()
    connected(seen)
    publisher.publish().channel(single).message('before').sync()
    eventually(lambda: a.eq(texts(seen), ['before'], 'message before unsubscribe'))

    # snippet.unsubscribe_subscription
    t1_subscription.unsubscribe()
    # snippet.end

    eventually(lambda: a.eq(pubnub.get_subscribed_channels(), [control], 'channels left'))
    publisher.publish().channel(single).message('after single').sync()
    publisher.publish().channel(control).message('after control').sync()
    eventually(lambda: a.contains(texts(seen), 'after control', 'the control channel still delivers'))
    a.not_contains(texts(seen), 'after single', 'no message after unsubscribe')


@step('unsubscribe_set', role='open')
def test_unsubscribe_set(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    first, second, control = [names.with_suffix(n) for n in ('ch1', 'ch2', 'ch3')]
    seen = attach(pubnub)
    pubnub.channel(control).subscription().subscribe()

    subscription_set = pubnub.subscription_set([
        pubnub.channel(first).subscription(),
        pubnub.channel(second).subscription()
    ])
    subscription_set.subscribe()
    connected(seen)
    publisher.publish().channel(first).message('before first').sync()
    publisher.publish().channel(second).message('before second').sync()
    eventually(lambda: a.eq(sorted(texts(seen)), ['before first', 'before second'], 'messages before unsubscribe'))

    # snippet.unsubscribe_set
    subscription_set.unsubscribe()
    # snippet.end

    eventually(lambda: a.eq(pubnub.get_subscribed_channels(), [control], 'channels left'))
    publisher.publish().channel(first).message('after first').sync()
    publisher.publish().channel(second).message('after second').sync()
    publisher.publish().channel(control).message('after control').sync()
    eventually(lambda: a.contains(texts(seen), 'after control', 'the control channel still delivers'))
    a.not_contains(texts(seen), 'after first', 'no message after unsubscribe')
    a.not_contains(texts(seen), 'after second', 'no message after unsubscribe')


@step('unsubscribe_all', role='open')
def test_unsubscribe_all(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    single, first = [names.with_suffix(n) for n in ('my_channel', 'ch1')]
    seen = attach(pubnub)
    pubnub.channel(single).subscription().subscribe()
    pubnub.subscription_set([pubnub.channel(first).subscription()]).subscribe()
    connected(seen)
    a.eq(sorted(pubnub.get_subscribed_channels()), sorted([single, first]))

    # snippet.unsubscribe_all
    pubnub.unsubscribe_all()
    # snippet.end

    # unsubscribe_all() leaves the registry unusable (see the report), so the harness must not call it again
    pubnub.subscribed_by_suite = False
    eventually(lambda: a.eq(pubnub.get_subscribed_channels(), [], 'channels left'))
    eventually(lambda: a.contains(seen.categories, PNStatusCategory.PNAcknowledgmentCategory, 'leave acknowledged'))
    publisher.publish().channel(single).message('after single').sync()
    publisher.publish().channel(first).message('after first').sync()
    a.eq(texts(seen), [], 'no message after unsubscribe_all')


class StatusCollector(Collector):
    """Collector that keeps the status objects, not only their categories."""

    def __init__(self):
        super().__init__()
        self.statuses = []

    def status(self, pubnub, status):
        super().status(pubnub, status)
        with self._lock:
            self.statuses.append(status)


def attach_status(client):
    collector = StatusCollector()
    client.subscribed_by_suite = True
    client.add_listener(collector)
    return collector


@step('subscribe_old_channel', role='open')
def test_subscribe_old_channel(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = names.with_suffix('my_channel')
    seen = attach_status(pubnub)

    # snippet.subscribe_old_channel
    pubnub.subscribe() \
        .channels('my_channel') \
        .execute()
    # snippet.end

    connected(seen)
    connect = [s for s in seen.statuses if s.category == PNStatusCategory.PNConnectedCategory][0]
    a.ok(not connect.is_error(), 'connected status is not an error')
    a.eq(connect.status_code, 200)
    a.eq(connect.error_data, None)
    envelope = publisher.publish().channel(name).message({'hello': 'old'}).meta({'k': 'v'}).sync()
    publisher.signal().channel(name).message('old signal').sync()
    eventually(lambda: a.eq(len(seen.messages), 1, 'messages received'))
    eventually(lambda: a.eq(len(seen.signals), 1, 'signals received'))
    message = seen.messages[0]
    a.eq((message.message, message.channel, message.subscription), ({'hello': 'old'}, name, None))
    a.eq((message.timetoken, message.user_metadata, message.publisher),
         (envelope.result.timetoken, {'k': 'v'}, publisher.uuid))
    signal = seen.signals[0]
    a.eq((signal.message, signal.channel, signal.publisher, signal.timetoken > 0),
         ('old signal', name, publisher.uuid, True))


@step('subscribe_old_multiple', role='open')
def test_subscribe_old_multiple(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    both = [names.with_suffix('my_channel1'), names.with_suffix('my_channel2')]
    seen = attach(pubnub)

    # snippet.subscribe_old_multiple
    pubnub.subscribe() \
        .channels(["my_channel1", "my_channel2"]) \
        .execute()
    # snippet.end

    connected(seen)
    for target in both:
        publisher.publish().channel(target).message(f'to {target}').sync()
    eventually(lambda: a.eq(sorted(texts(seen)), sorted(f'to {t}' for t in both), 'both channels deliver'))


@step('subscribe_old_wildcard', role='open')
def test_subscribe_old_wildcard(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    matching = f"foo.{names.with_suffix('bar')}"
    seen = attach(pubnub)

    # snippet.subscribe_old_wildcard
    pubnub.subscribe() \
        .channels("foo.*") \
        .execute()
    # snippet.end

    connected(seen)
    publisher.publish().channel(matching).message('wildcard hit').sync()
    eventually(lambda: a.contains(texts(seen), 'wildcard hit', 'wildcard delivers'))
    hit = [m for m in seen.messages if m.message == 'wildcard hit'][0]
    a.eq((hit.channel, hit.subscription), (matching, 'foo.*'))


@step('subscribe_old_group', role='open')
def test_subscribe_old_group(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    group_name = names.with_suffix('awesome_channel_group')
    grouped = names.with_suffix('grouped_channel')
    publisher.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).sync()
    world.record('channel_group', group_name)
    seen = attach(pubnub)

    # snippet.subscribe_old_group
    pubnub.subscribe() \
        .channel_groups("awesome_channel_group") \
        .execute()
    # snippet.end

    connected(seen)
    publisher.publish().channel(grouped).message('group hit').sync()
    eventually(lambda: a.eq(texts(seen), ['group hit'], 'group delivers'))
    a.eq((seen.messages[0].channel, seen.messages[0].subscription), (grouped, group_name))


@step('subscribe_old_presence', 'subscribe_old_group_presence', role='open')
def test_subscribe_old_presence(clients):
    pubnub = clients.sync('open', 'subscriber')
    name = names.with_suffix('my_channel')
    group_name = names.with_suffix('awesome_channel_group')
    grouped = names.with_suffix('grouped_channel')
    clients.sync('open', 'publisher').add_channel_to_channel_group().channels([grouped]) \
        .channel_group(group_name).sync()
    world.record('channel_group', group_name)
    seen = attach(pubnub)

    # snippet.subscribe_old_presence
    pubnub.subscribe()\
        .channels("my_channel")\
        .with_presence()\
        .execute()
    # snippet.end

    # snippet.subscribe_old_group_presence
    pubnub.subscribe() \
        .channel_groups("awesome_channel_group") \
        .with_presence() \
        .execute()
    # snippet.end

    connected(seen)
    other = clients.sync('open', 'second_user')
    listen(other, name)
    eventually(lambda: a.contains([(p.event, p.channel) for p in seen.presence_events if p.uuid == other.uuid],
                                  ('join', name), 'join on the channel'))
    # Presence of a channel group is announced per member channel: a client that subscribes to the group itself
    # produces no join, a client that subscribes to a member channel does, and the event carries the group in
    # `subscription` (workers.py _process_incoming_payload, subscription_match with the -pnpres suffix stripped).
    member = clients.sync('open', 'member_user')
    listen(member, grouped)
    eventually(lambda: a.contains([(p.event, p.channel, p.subscription) for p in seen.presence_events
                                   if p.uuid == member.uuid],
                                  ('join', grouped, group_name), 'join of a member channel through the group'))
    join = [p for p in seen.presence_events if p.event == 'join' and p.uuid == other.uuid and p.channel == name][0]
    a.ok(isinstance(join.timestamp, int) and join.occupancy >= 1, 'join carries timestamp and occupancy')


@step('subscribe_old_state', role='open')
def test_subscribe_old_state(clients):
    pubnub = clients.sync('open', 'subscriber')
    name = names.with_suffix('my_channel')

    # snippet.subscribe_old_state
    from pubnub.enums import PNStatusCategory
    from pubnub.pubnub import SubscribeListener

    class MySubscribeListener(SubscribeListener):
        def status(self, pubnub, status):
            if status.category == PNStatusCategory.PNConnectedCategory:
                state = {
                    'field_a': 'awesome',
                    'field_b': 10
                }
                envelope = pubnub.set_state().channels('my_channel').state(state).sync()
                print(f'State set: {envelope.result.state}')
            else:
                pass

        def message(self, pubnub, message):
            pass

        def presence(self, pubnub, presence):
            pass

    my_listener = MySubscribeListener()
    pubnub.add_listener(my_listener)

    pubnub.subscribe().channels("my_channel").execute()
    # snippet.end

    pubnub.subscribed_by_suite = True
    reader = clients.sync('open', 'reader')

    def read_state():
        return reader.get_state().channels(name).uuid(pubnub.uuid).sync().result.channels

    eventually(lambda: a.eq(read_state(), {name: {'field_a': 'awesome', 'field_b': 10}},
                            'state set from the status callback'))
    here = reader.here_now().channels(name).include_state(True).sync().result
    a.eq([(o.uuid, o.state) for o in here.channels[0].occupants],
         [(pubnub.uuid, {'field_a': 'awesome', 'field_b': 10})])


@compile_only('subscribe_old_logging', reason='DEBUG logging writes every request URL with the keys to the output')
def logging_sample():
    # snippet.subscribe_old_logging
    import logging
    import pubnub

    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub, SubscribeListener

    pubnub.set_stream_logger('pubnub', logging.DEBUG)

    pnconfig = PNConfiguration()

    pnconfig.subscribe_key = 'demo'
    pnconfig.publish_key = 'demo'
    pnconfig.user_id = 'my_custom_user_id'

    pubnub = PubNub(pnconfig)

    pubnub.add_listener(SubscribeListener())
    pubnub.subscribe().channels("my_channel").execute()
    # snippet.end
    return pubnub


@step('listeners_old_add', role='open')
def test_listeners_old_add(clients, capsys):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = names.with_suffix('my_channel')
    printed = Printed(capsys)
    seen = attach(pubnub)

    # snippet.listeners_old_add
    from pubnub.callbacks import SubscribeCallback
    from pubnub.enums import PNOperationType, PNStatusCategory

    class MySubscribeCallback(SubscribeCallback):
        def message(self, pubnub, message):
            print("Message channel: %s" % message.channel)
            print("Message subscription: %s" % message.subscription)
            print("Message timetoken: %s" % message.timetoken)
            print("Message payload: %s" % message.message)
            print("Message publisher: %s" % message.publisher)

        def presence(self, pubnub, presence):
            # Can be join, leave, state-change, timeout, or interval
            print("Presence event: %s" % presence.event)

            # The channel to which the message was published
            print("Presence channel: %s" % presence.channel)

            # Number of users subscribed to the channel
            print("Presence occupancy: %s" % presence.occupancy)

            # User state
            print("Presence state: %s" % presence.state)

            # Channel group or wildcard subscription match, if any
            print("Presence subscription: %s" % presence.subscription)

            # UUID to which this event is related
            print("Presence UUID: %s" % presence.uuid)

            # Publish timetoken
            print("Presence timestamp: %s" % presence.timestamp)

            # Current timetoken
            print("Presence timetoken: %s" % presence.timetoken)

            # List of users that have joined the channel (if event is 'interval')
            print("Presence joined: %s" % presence.join)

            # List of users that have left the channel (if event is 'interval')
            print("Presence left: %s" % presence.leave)

            # List of users that have timed-out off the channel (if event is 'interval')
            print("Presence timed out: %s" % presence.timeout)

        def status(self, pubnub, status):
            # The status object returned is always related to subscribe but could contain
            # information about subscribe, heartbeat, or errors
            # use the operationType to switch on different options
            if status.operation == PNOperationType.PNSubscribeOperation \
                    or status.operation == PNOperationType.PNUnsubscribeOperation:
                if status.category == PNStatusCategory.PNConnectedCategory:
                    pass
                    # This is expected for a subscribe, this means there is no error or issue whatsoever
                elif status.category == PNStatusCategory.PNReconnectedCategory:
                    pass
                    # This usually occurs if subscribe temporarily fails but reconnects. This means
                    # there was an error but there is no longer any issue
                elif status.category == PNStatusCategory.PNDisconnectedCategory:
                    pass
                    # This is the expected category for an unsubscribe. This means there
                    # was no error in unsubscribing from everything
                elif status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
                    pass
                    # This is usually an issue with the internet connection, this is an error, handle
                    # appropriately retry will be called automatically
                elif status.category == PNStatusCategory.PNAccessDeniedCategory:
                    pass
                    # This means that Access Manager does not allow this client to subscribe to this
                    # channel and channel group configuration. This is another explicit error
                else:
                    pass
                    # This is usually an issue with the internet connection, this is an error, handle appropriately
                    # retry will be called automatically
            else:
                pass
                # Encountered unknown status type

        def signal(self, pubnub, signal):
            print("Signal channel: %s" % signal.channel)
            print("Signal subscription: %s" % signal.subscription)
            print("Signal timetoken: %s" % signal.timetoken)
            print("Signal payload: %s" % signal.message)
            print("Signal publisher: %s" % signal.publisher)

        def message_action(self, pubnub, message_action):
            print("Message action type: %s" % message_action.type)
            print("Message action value: %s" % message_action.value)
            print("Message action uuid: %s" % message_action.uuid)
            print("Message action action_timetoken: %s" % message_action.action_timetoken)
            print("Message action message_timetoken: %s" % message_action.message_timetoken)

    pubnub.add_listener(MySubscribeCallback())
    # snippet.end

    pubnub.subscribe().channels(name).with_presence().execute()
    connected(seen)
    envelope = publisher.publish().channel(name).message({'n': 1}).sync()
    publisher.signal().channel(name).message('sig').sync()
    action = PNMessageAction().create(type='reaction', value='smile', message_timetoken=envelope.result.timetoken)
    publisher.add_message_action().channel(name).message_action(action).sync()
    other = clients.sync('open', 'second_user')
    listen(other, name)
    for text in (f'Message channel: {name}', "Message payload: {'n': 1}", f'Message publisher: {publisher.uuid}',
                 f'Message timetoken: {envelope.result.timetoken}', 'Signal payload: sig',
                 'Message action type: reaction', 'Message action value: smile',
                 f'Message action message_timetoken: {envelope.result.timetoken}',
                 'Presence event: join', f'Presence channel: {name}', f'Presence UUID: {other.uuid}'):
        eventually(lambda: a.contains(printed.text(), text, 'printed by the docs listener'))
    a.ok(len(seen.messages) == 1)


@step('listeners_old_remove', role='open')
def test_listeners_old_remove(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = names.with_suffix('my_channel')
    keeper = attach(pubnub)

    class MySubscribeCallback(Collector):
        pass

    # snippet.listeners_old_remove
    my_listener = MySubscribeCallback()

    pubnub.add_listener(my_listener)

    # some time later
    pubnub.remove_listener(my_listener)
    # snippet.end

    pubnub.add_listener(my_listener)
    pubnub.subscribe().channels(name).execute()
    connected(keeper)
    publisher.publish().channel(name).message('first').sync()
    eventually(lambda: a.eq(texts(keeper), ['first'], 'the kept listener receives'))
    eventually(lambda: a.eq(texts(my_listener), ['first'], 'a listener that is added receives'))
    pubnub.remove_listener(my_listener)
    publisher.publish().channel(name).message('second').sync()
    eventually(lambda: a.eq(texts(keeper), ['first', 'second'], 'the kept listener still receives'))
    a.eq(texts(my_listener), ['first'], 'a removed listener receives nothing more')


@step('listeners_old_disconnects', role='open')
def test_listeners_old_disconnects(clients, caplog):
    pubnub = clients.sync('open', 'subscriber')
    seen = attach(pubnub)

    # snippet.listeners_old_disconnects
    import logging

    from pubnub.callbacks import SubscribeCallback
    from pubnub.enums import PNStatusCategory

    logger = logging.getLogger(__name__)

    class HandleDisconnectsCallback(SubscribeCallback):
        def status(self, pubnub, status):
            if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
                # internet got lost, do some magic and call reconnect when ready
                pubnub.reconnect()
            elif status.category == PNStatusCategory.PNTimeoutCategory:
                # do some magic and call reconnect when ready
                pubnub.reconnect()
            else:
                logger.debug(status)

        def presence(self, pubnub, presence):
            pass

        def message(self, pubnub, message):
            pass

        def signal(self, pubnub, signal):
            pass

    disconnect_listener = HandleDisconnectsCallback()

    pubnub.add_listener(disconnect_listener)
    # snippet.end

    with caplog.at_level(logging.DEBUG):
        pubnub.subscribe().channels(names.with_suffix('my_channel')).execute()
        connected(seen)
        eventually(lambda: a.ok(any('PNConnectedCategory' in r.getMessage() or 'PNStatus' in r.getMessage()
                                    for r in caplog.records if r.name == __name__ or r.name.endswith('subscribe')),
                                'the docs logger saw the connected status'))


@step('unsubscribe_old_channel', role='open')
def test_unsubscribe_old_channel(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    single, control = names.with_suffix('my_channel'), names.with_suffix('ch3')
    seen = attach(pubnub)
    observer = listen(clients.sync('open', 'observer'), single, presence=True)
    pubnub.subscribe().channels([single, control]).execute()
    connected(seen)
    publisher.publish().channel(single).message('before').sync()
    eventually(lambda: a.eq(texts(seen), ['before'], 'message before unsubscribe'))

    # snippet.unsubscribe_old_channel
    pubnub.unsubscribe() \
        .channels("my_channel") \
        .execute()
    # snippet.end

    eventually(lambda: a.eq(pubnub.get_subscribed_channels(), [control], 'channels left'))
    publisher.publish().channel(single).message('after single').sync()
    publisher.publish().channel(control).message('after control').sync()
    eventually(lambda: a.contains(texts(seen), 'after control', 'the control channel still delivers'))
    a.not_contains(texts(seen), 'after single', 'no message after unsubscribe')
    eventually(lambda: a.contains([(p.event, p.uuid) for p in observer.presence_events], ('leave', pubnub.uuid),
                                  'leave event'))
    leave = [p for p in observer.presence_events if p.event == 'leave' and p.uuid == pubnub.uuid][0]
    a.ok(isinstance(leave.timestamp, int) and isinstance(leave.occupancy, int), 'leave carries timestamp, occupancy')


@step('unsubscribe_old_multiple', 'unsubscribe_old_group', role='open')
def test_unsubscribe_old_multiple_and_group(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    both = [names.with_suffix('my_channel1'), names.with_suffix('my_channel2')]
    groups = [names.with_suffix('my_group1'), names.with_suffix('my_group2')]
    control = names.with_suffix('ch3')
    grouped = [names.with_suffix('grouped_one'), names.with_suffix('grouped_two')]
    for group_name, channel_name in zip(groups, grouped):
        publisher.add_channel_to_channel_group().channels([channel_name]).channel_group(group_name).sync()
        world.record('channel_group', group_name)
    seen = attach(pubnub)
    pubnub.subscribe().channels(both + [control]).channel_groups(groups).execute()
    connected(seen)
    for target in both + grouped:
        publisher.publish().channel(target).message(f'before {target}').sync()
    eventually(lambda: a.eq(len(seen.messages), 4, 'messages before unsubscribe'))

    # snippet.unsubscribe_old_multiple
    pubnub.unsubscribe() \
        .channels(["my_channel1", "my_channel2"]) \
        .execute()
    # snippet.end

    # snippet.unsubscribe_old_group
    pubnub.unsubscribe() \
        .channel_groups(["my_group1", "my_group2"]) \
        .execute()
    # snippet.end

    eventually(lambda: a.eq((pubnub.get_subscribed_channels(), pubnub.get_subscribed_channel_groups()),
                            ([control], []), 'subscriptions left'))
    for target in both + grouped + [control]:
        publisher.publish().channel(target).message(f'after {target}').sync()
    eventually(lambda: a.contains(texts(seen), f'after {control}', 'the control channel still delivers'))
    a.eq(sorted(m for m in texts(seen) if m.startswith('after')), [f'after {control}'], 'nothing else after')


@step('unsubscribe_all_old', role='open')
def test_unsubscribe_all_old(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    single = names.with_suffix('my_channel')
    group_name = names.with_suffix('my_group1')
    grouped = names.with_suffix('grouped_one')
    publisher.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).sync()
    world.record('channel_group', group_name)
    seen = attach(pubnub)
    pubnub.subscribe().channels(single).channel_groups(group_name).execute()
    connected(seen)
    a.eq((pubnub.get_subscribed_channels(), pubnub.get_subscribed_channel_groups()), ([single], [group_name]))

    # snippet.unsubscribe_all_old
    pubnub.unsubscribe_all()
    # snippet.end

    # unsubscribe_all() leaves the registry unusable (see the report), so the harness must not call it again
    pubnub.subscribed_by_suite = False
    eventually(lambda: a.eq((pubnub.get_subscribed_channels(), pubnub.get_subscribed_channel_groups()), ([], []),
                            'subscriptions left'))
    eventually(lambda: a.contains(seen.categories, PNStatusCategory.PNAcknowledgmentCategory, 'leave acknowledged'))
    publisher.publish().channel(single).message('after single').sync()
    publisher.publish().channel(grouped).message('after group').sync()
    a.eq(texts(seen), [], 'no message after unsubscribe_all')
