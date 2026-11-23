"""Docs page: subscribe-legacy (sync). The samples of the legacy page, moved from the old
docs-snippets/sync/subscribe.py.
"""
import io
import sys
from logging import DEBUG, getLogger

from pubnub.enums import PNStatusCategory
from pubnub.models.consumer.message_actions import PNMessageAction

from support import assertions as a
from support import cleanup as live_cleanup
from support.env import use_open_keys
from support.listen import Collector, listen
from support.wait import PRESENCE_EVENT_TIMEOUT, PRESENCE_TIMEOUT, eventually
from shared.presence import not_present
from shared.subscribe import Printed, attach, attach_status, connected, texts


def test_subscribe_old_channel(clients):
    """Snippet: subscribe_old_channel."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = 'my_channel'
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


def test_subscribe_old_multiple(clients):
    """Snippet: subscribe_old_multiple."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    both = ['my_channel1', 'my_channel2']
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


def test_subscribe_old_wildcard(clients):
    """Snippet: subscribe_old_wildcard."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    matching = f"foo.{'bar'}"
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


def test_subscribe_old_group(clients):
    """Snippet: subscribe_old_group."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    group_name = 'awesome_channel_group'
    grouped = 'grouped_channel'
    publisher.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).sync()
    live_cleanup.record('channel_group', group_name)
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


def test_subscribe_old_presence(clients):
    """Snippets: subscribe_old_presence, subscribe_old_group_presence."""
    pubnub = clients.sync('open', 'subscriber')
    name = 'my_channel'
    group_name = 'awesome_channel_group'
    grouped = 'grouped_channel'
    clients.sync('open', 'publisher').add_channel_to_channel_group().channels([grouped]) \
        .channel_group(group_name).sync()
    live_cleanup.record('channel_group', group_name)
    # A join is emitted only for a user ID that is not an occupant yet (an earlier test can leave one listed).
    not_present(name, ['second_user'])
    not_present(grouped, ['member_user'])
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
                                  ('join', name), 'join on the channel'), timeout=PRESENCE_EVENT_TIMEOUT)
    # Presence of a channel group is announced per member channel: a client that subscribes to the group itself
    # produces no join, a client that subscribes to a member channel does, and the event carries the group in
    # `subscription` (workers.py _process_incoming_payload, subscription_match with the -pnpres suffix stripped).
    member = clients.sync('open', 'member_user')
    listen(member, grouped)
    eventually(lambda: a.contains([(p.event, p.channel, p.subscription) for p in seen.presence_events
                                   if p.uuid == member.uuid],
                                  ('join', grouped, group_name), 'join of a member channel through the group'),
               timeout=PRESENCE_EVENT_TIMEOUT)
    join = [p for p in seen.presence_events if p.event == 'join' and p.uuid == other.uuid and p.channel == name][0]
    a.ok(isinstance(join.timestamp, int) and join.occupancy >= 1, 'join carries timestamp and occupancy')


def test_subscribe_old_state(clients):
    """Snippet: subscribe_old_state."""
    pubnub = clients.sync('open', 'subscriber')
    name = 'my_channel'

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

    def listed_with_state():
        here = reader.here_now().channels(name).include_state(True).sync().result
        # Other user IDs can still be listed on the shared channel, so only the own occupant is checked.
        a.contains([(o.uuid, o.state) for o in here.channels[0].occupants],
                   (pubnub.uuid, {'field_a': 'awesome', 'field_b': 10}))
    eventually(listed_with_state, timeout=PRESENCE_TIMEOUT, what='here_now lists the state')


def test_subscribe_old_logging(clients, caplog, monkeypatch):
    """Snippet: subscribe_old_logging.

    DEBUG logs carry every request URL with the keys. The handler of the sample writes to a buffer that replaces
    sys.stderr, the caplog handler takes DEBUG records for the assertions only, and the report handler stays at the
    INFO level of pytest.ini, so no key reaches the output.
    """
    logger = getLogger('pubnub')
    handlers = list(logger.handlers)
    sample_stderr = io.StringIO()
    monkeypatch.setattr(sys, 'stderr', sample_stderr)
    caplog.set_level(DEBUG, logger='pubnub')
    try:
        # snippet.subscribe_old_logging
        import logging
        import pubnub

        from pubnub.pnconfiguration import PNConfiguration
        from pubnub.pubnub import PubNub, SubscribeListener

        pubnub.set_stream_logger('pubnub', logging.DEBUG)

        pnconfig = PNConfiguration()

        pnconfig.subscribe_key = 'demo'
        pnconfig.publish_key = 'demo'
        # snippet.hide
        use_open_keys(pnconfig)
        # snippet.show
        pnconfig.user_id = 'my_custom_user_id'

        pubnub = PubNub(pnconfig)

        pubnub.add_listener(SubscribeListener())
        pubnub.subscribe().channels("my_channel").execute()
        # snippet.end
        clients.track(pubnub)

        def subscribe_logged():
            records = [r for r in caplog.records if r.name == 'pubnub' and r.levelno == DEBUG]
            a.ok(any('/v2/subscribe/' in r.getMessage() for r in records), 'a DEBUG record of the subscribe request')
            a.ok('[DEBUG]' in sample_stderr.getvalue() and '/v2/subscribe/' in sample_stderr.getvalue(),
                 'the stream handler of set_stream_logger writes the subscribe request')
        eventually(subscribe_logged)
        a.eq(pubnub.get_subscribed_channels(), ['my_channel'])
        pubnub.unsubscribe_all()
    finally:
        for handler in logger.handlers:
            if handler not in handlers:
                logger.removeHandler(handler)


def test_listeners_old_add(clients, capsys):
    """Snippet: listeners_old_add."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = 'my_channel'
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


def test_listeners_old_remove(clients):
    """Snippet: listeners_old_remove."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    name = 'my_channel'
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


def test_listeners_old_disconnects(clients, caplog):
    """Snippet: listeners_old_disconnects."""
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
        pubnub.subscribe().channels('my_channel').execute()
        connected(seen)
        eventually(lambda: a.ok(any('PNConnectedCategory' in r.getMessage() or 'PNStatus' in r.getMessage()
                                    for r in caplog.records if r.name == __name__ or r.name.endswith('subscribe')),
                                'the docs logger saw the connected status'))


def test_unsubscribe_old_channel(clients):
    """Snippet: unsubscribe_old_channel."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    single, control = 'my_channel', 'ch3'
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


def test_unsubscribe_old_multiple(clients):
    """Snippets: unsubscribe_old_multiple, unsubscribe_old_group."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    both = ['my_channel1', 'my_channel2']
    groups = ['my_group1', 'my_group2']
    control = 'ch3'
    grouped = ['grouped_one', 'grouped_two']
    for group_name, channel_name in zip(groups, grouped):
        publisher.add_channel_to_channel_group().channels([channel_name]).channel_group(group_name).sync()
        live_cleanup.record('channel_group', group_name)
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


def test_unsubscribe_all_old(clients):
    """Snippet: unsubscribe_all_old."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    single = 'my_channel'
    group_name = 'my_group1'
    grouped = 'grouped_one'
    publisher.add_channel_to_channel_group().channels([grouped]).channel_group(group_name).sync()
    live_cleanup.record('channel_group', group_name)
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
