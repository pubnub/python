from types import SimpleNamespace

from pubnub.models.consumer.objects_v2.channel import PNChannelMetadataResult
from pubnub.models.consumer.objects_v2.memberships import PNMembershipResult
from pubnub.models.consumer.objects_v2.uuid import PNUUIDMetadataResult
from pubnub.models.consumer.pubsub import PNMessageActionResult
from pubnub.models.server.subscribe import SubscribeMessage
from pubnub.workers import BaseMessageWorker


class RecordingListenerManager:
    def __init__(self):
        self.announced = []

    def announce_channel(self, result):
        self.announced.append(('channel', result))

    def announce_uuid(self, result):
        self.announced.append(('uuid', result))

    def announce_membership(self, result):
        self.announced.append(('membership', result))

    def announce_message_action(self, result):
        self.announced.append(('message_action', result))


def make_worker():
    worker = BaseMessageWorker(SimpleNamespace(config=SimpleNamespace(cipher_key=None)))
    worker._listener_manager = RecordingListenerManager()
    return worker


def envelope(channel, payload, message_type, subscription=None):
    json_input = {
        'c': channel,
        'd': payload,
        'f': 0,
        'i': 'publisher-1',
        'k': 'sub-key',
        'p': {'t': '17000000000000000', 'r': 1},
        'e': message_type,
    }
    if subscription is not None:
        json_input['b'] = subscription
    return SubscribeMessage.from_json(json_input)


def action_payload(event):
    return {
        'source': 'actions',
        'version': '1.0',
        'event': event,
        'data': {
            'type': 'reaction',
            'value': 'smiley_face',
            'messageTimetoken': '16999999999999999',
            'actionTimetoken': '17000000000000000',
            'uuid': 'user-1',
        },
    }


def test_message_action_event_kind_added():
    worker = make_worker()

    worker._process_incoming_payload(envelope('ch1', action_payload('added'), BaseMessageWorker.TYPE_MESSAGE_ACTION))

    kind, result = worker._listener_manager.announced[0]
    assert kind == 'message_action'
    assert isinstance(result, PNMessageActionResult)
    assert result.event == 'added'
    assert result.type == 'reaction'
    assert result.value == 'smiley_face'
    assert result.channel == 'ch1'


def test_message_action_event_kind_removed():
    worker = make_worker()

    worker._process_incoming_payload(envelope('ch1', action_payload('removed'), BaseMessageWorker.TYPE_MESSAGE_ACTION))

    _, result = worker._listener_manager.announced[0]
    assert result.event == 'removed'


def test_message_action_result_defaults_event_to_none():
    result = PNMessageActionResult(action_payload('added')['data'])

    assert result.event is None


def test_app_context_results_carry_channel_and_subscription():
    worker = make_worker()
    cases = [
        ('channel', PNChannelMetadataResult),
        ('uuid', PNUUIDMetadataResult),
        ('membership', PNMembershipResult),
    ]

    for object_type, result_class in cases:
        payload = {'source': 'objects', 'version': '2.0', 'event': 'set', 'type': object_type, 'data': {'id': 'x'}}
        worker._process_incoming_payload(envelope('ch1', payload, BaseMessageWorker.TYPE_OBJECT))
        worker._process_incoming_payload(envelope('ch2', payload, BaseMessageWorker.TYPE_OBJECT,
                                                  subscription='group1'))

    announced = worker._listener_manager.announced
    assert [kind for kind, _ in announced] == ['channel', 'channel', 'uuid', 'uuid', 'membership', 'membership']
    for index, (_, result_class) in enumerate(cases):
        direct = announced[index * 2][1]
        via_group = announced[index * 2 + 1][1]
        assert isinstance(direct, result_class)
        assert direct.event == 'set'
        assert direct.channel == 'ch1'
        assert direct.subscription is None
        assert via_group.channel == 'ch2'
        assert via_group.subscription == 'group1'
