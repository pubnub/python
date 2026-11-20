"""Docs page: mobile push (sync). Source: docs/sdks/python/api-reference/mobile-push.md.

Only the registration side is testable. A push is delivered by FCM or APNs to a real device, so delivery is not tested.
The device tokens are made up and unique per run, and every gateway is cleaned in a finally block.
"""
import secrets

from pubnub.enums import PNPushEnvironment, PNPushType

from harness import assertions as a
from harness import names
from harness.step import step
from harness.wait import eventually

REGISTERED_NAMES = ['deviceId']
TOPIC = 'myapptopic'
# An APNs token is hex. The docs example uses 32 hex characters, a real device token has 64.
APNS2_DEVICE = secrets.token_hex(32)
CHANNELS = ['ch1', 'ch2', 'ch3']


def suffixed(channels):
    return sorted(names.with_suffix(c) for c in channels)


def fcm_device():
    return names.with_suffix('deviceId')


def registered(pubnub, push_type):
    """Channels the service holds for the device on one gateway."""
    if push_type == PNPushType.APNS2:
        envelope = pubnub.list_push_channels().push_type(push_type).device_id(APNS2_DEVICE) \
            .topic(TOPIC).environment(PNPushEnvironment.DEVELOPMENT).sync()
    else:
        envelope = pubnub.list_push_channels().push_type(push_type).device_id(fcm_device()).sync()
    return sorted(envelope.result.channels)


def seed(pubnub, channels):
    channels = suffixed(channels)
    pubnub.add_channels_to_push().push_type(PNPushType.FCM).channels(channels).device_id(fcm_device()).sync()
    pubnub.add_channels_to_push().push_type(PNPushType.APNS2).channels(channels).device_id(APNS2_DEVICE) \
        .topic(TOPIC).environment(PNPushEnvironment.DEVELOPMENT).sync()


def clear(pubnub):
    """Remove the test tokens on every gateway and environment so that nothing outlives the run."""
    for push_type in (PNPushType.FCM, PNPushType.GCM):
        try:
            pubnub.remove_device_from_push().push_type(push_type).device_id(fcm_device()).sync()
        except Exception as e:  # cleanup must never hide the real failure
            print('cleanup: could not clear a gateway (' + type(e).__name__ + ')')
    for push_type in (PNPushType.APNS, PNPushType.APNS2):
        for environment in (PNPushEnvironment.DEVELOPMENT, PNPushEnvironment.PRODUCTION):
            try:
                pubnub.remove_device_from_push().push_type(push_type).device_id(APNS2_DEVICE) \
                    .topic(TOPIC).environment(environment).sync()
            except Exception as e:
                print('cleanup: could not clear a gateway (' + type(e).__name__ + ')')


def expect(pubnub, fcm, apns2, what):
    eventually(lambda: a.eq(registered(pubnub, PNPushType.FCM), fcm, 'fcm ' + what))
    eventually(lambda: a.eq(registered(pubnub, PNPushType.APNS2), apns2, 'apns2 ' + what))


@step('add_channels_to_push_builder', 'add_channels_to_push_named', role='open')
def test_add_channels_to_push(clients):
    pubnub = clients.sync('open', 'push_registrar')
    try:
        a.ok(len(APNS2_DEVICE) == 64 and set(APNS2_DEVICE) <= set('0123456789abcdef'), 'apns2 token is 64 hex chars')

        # snippet.add_channels_to_push_builder
        # For FCM
        pubnub.add_channels_to_push() \
            .push_type(PNPushType.FCM) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id("deviceId") \
            .sync()

        # For APNS2 device token should be hex
        pubnub.add_channels_to_push() \
            .push_type(PNPushType.APNS2) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id(APNS2_DEVICE) \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()
        # snippet.end
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after add (builder)')
        clear(pubnub)
        expect(pubnub, [], [], 'after clearing')

        # snippet.add_channels_to_push_named
        # For FCM
        pubnub.add_channels_to_push(
            push_type=PNPushType.FCM,
            channels=["ch1", "ch2", "ch3"],
            device_id="deviceId"
        ).sync()

        # For APNS2
        pubnub.add_channels_to_push(
            push_type=PNPushType.APNS2,
            channels=["ch1", "ch2", "ch3"],
            device_id=APNS2_DEVICE,
            topic="myapptopic",
            environment=PNPushEnvironment.DEVELOPMENT
        ).sync()
        # snippet.end
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after add (named)')
    finally:
        clear(pubnub)


@step('list_push_channels_builder', 'list_push_channels_named', role='open')
def test_list_push_channels(clients):
    pubnub = clients.sync('open', 'push_lister')
    try:
        seed(pubnub, CHANNELS)
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding')

        # snippet.list_push_channels_builder
        # For FCM
        envelope = pubnub.list_push_channels() \
            .push_type(PNPushType.FCM) \
            .device_id("deviceId") \
            .sync()
        fcm_channels = envelope.result.channels

        # For APNS2
        envelope = pubnub.list_push_channels() \
            .push_type(PNPushType.APNS2) \
            .device_id(APNS2_DEVICE) \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()
        apns2_channels = envelope.result.channels
        # snippet.end
        a.eq(sorted(fcm_channels), suffixed(CHANNELS), 'fcm channels listed')
        a.eq(sorted(apns2_channels), suffixed(CHANNELS), 'apns2 channels listed')
        a.ok(not envelope.status.is_error(), 'status is not an error')

        # snippet.list_push_channels_named
        # For FCM
        envelope = pubnub.list_push_channels(push_type=PNPushType.FCM, device_id="deviceId").sync()
        fcm_channels = envelope.result.channels

        # For APNS2
        envelope = pubnub.list_push_channels(push_type=PNPushType.APNS2,
                                             device_id=APNS2_DEVICE,
                                             topic="myapptopic",
                                             environment=PNPushEnvironment.DEVELOPMENT) \
            .sync()
        apns2_channels = envelope.result.channels
        # snippet.end
        a.eq(sorted(fcm_channels), suffixed(CHANNELS), 'fcm channels listed (named)')
        a.eq(sorted(apns2_channels), suffixed(CHANNELS), 'apns2 channels listed (named)')

        # A device nothing was registered for lists no channels
        other = pubnub.list_push_channels().push_type(PNPushType.FCM).device_id(names.with_suffix('unknown')).sync()
        a.eq(other.result.channels, [], 'unknown device')
    finally:
        clear(pubnub)


@step('remove_channels_from_push_builder', 'remove_channels_from_push_named', role='open')
def test_remove_channels_from_push(clients):
    pubnub = clients.sync('open', 'push_remover')
    keep = 'keep_me'
    try:
        seed(pubnub, CHANNELS + [keep])
        expect(pubnub, suffixed(CHANNELS + [keep]), suffixed(CHANNELS + [keep]), 'after seeding')

        # snippet.remove_channels_from_push_builder
        # For FCM
        envelope = pubnub.remove_channels_from_push() \
            .push_type(PNPushType.FCM) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id("deviceId") \
            .sync()

        # For APNS2
        envelope = pubnub.remove_channels_from_push() \
            .push_type(PNPushType.APNS2) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id(APNS2_DEVICE) \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        expect(pubnub, suffixed([keep]), suffixed([keep]), 'after remove (builder), only the other channel is left')

        seed(pubnub, CHANNELS)
        expect(pubnub, suffixed(CHANNELS + [keep]), suffixed(CHANNELS + [keep]), 'after seeding again')

        # snippet.remove_channels_from_push_named
        # For FCM
        envelope = pubnub.remove_channels_from_push(channels=["ch1", "ch2", "ch3"],
                                                    push_type=PNPushType.FCM,
                                                    device_id="deviceId") \
            .sync()

        # For APNS2
        envelope = pubnub.remove_channels_from_push(channels=["ch1", "ch2", "ch3"],
                                                    push_type=PNPushType.APNS2,
                                                    device_id=APNS2_DEVICE,
                                                    topic="myapptopic",
                                                    environment=PNPushEnvironment.DEVELOPMENT) \
            .sync()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        expect(pubnub, suffixed([keep]), suffixed([keep]), 'after remove (named), only the other channel is left')
    finally:
        clear(pubnub)


@step('remove_device_from_push_builder', 'remove_device_from_push_named', role='open')
def test_remove_device_from_push(clients):
    pubnub = clients.sync('open', 'push_device_remover')
    try:
        seed(pubnub, CHANNELS)
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding')

        # snippet.remove_device_from_push_builder
        # For FCM
        envelope = pubnub.remove_device_from_push() \
            .push_type(PNPushType.FCM) \
            .device_id("deviceId") \
            .sync()

        # For APNS2
        envelope = pubnub.remove_device_from_push() \
            .push_type(PNPushType.APNS2) \
            .device_id(APNS2_DEVICE) \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        expect(pubnub, [], [], 'after remove all (builder)')

        seed(pubnub, CHANNELS)
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding again')

        # snippet.remove_device_from_push_named
        # For FCM
        envelope = pubnub.remove_device_from_push(device_id="deviceId", push_type=PNPushType.FCM).sync()

        # For APNS2
        envelope = pubnub.remove_device_from_push(device_id=APNS2_DEVICE,
                                                  push_type=PNPushType.APNS2,
                                                  topic="myapptopic",
                                                  environment=PNPushEnvironment.DEVELOPMENT) \
            .sync()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        expect(pubnub, [], [], 'after remove all (named)')
    finally:
        clear(pubnub)
