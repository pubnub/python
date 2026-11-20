"""Docs page: mobile push (asyncio). Source: docs/sdks/asyncio/api-reference/mobile-push.md.

Only the registration side is testable. A push is delivered by FCM or APNs to a real device, so delivery is not tested.
The device tokens are made up and unique per run, and every gateway is cleaned in a finally block.
"""
import secrets

from pubnub.enums import PNPushEnvironment, PNPushType

from harness import assertions as a
from harness import names
from harness.step import step
from harness.wait import aeventually

REGISTERED_NAMES = ['deviceId']
TOPIC = 'myapptopic'
APNS2_DEVICE = secrets.token_hex(32)
CHANNELS = ['ch1', 'ch2', 'ch3']


def suffixed(channels):
    return sorted(names.with_suffix(c) for c in channels)


def fcm_device():
    return names.with_suffix('deviceId')


async def registered(pubnub, push_type):
    """Channels the service holds for the device on one gateway."""
    if push_type == PNPushType.APNS2:
        envelope = await pubnub.list_push_channels().push_type(push_type).device_id(APNS2_DEVICE) \
            .topic(TOPIC).environment(PNPushEnvironment.DEVELOPMENT).future()
    else:
        envelope = await pubnub.list_push_channels().push_type(push_type).device_id(fcm_device()).future()
    return sorted(envelope.result.channels)


async def seed(pubnub, channels):
    channels = suffixed(channels)
    await pubnub.add_channels_to_push().push_type(PNPushType.FCM).channels(channels).device_id(fcm_device()).future()
    await pubnub.add_channels_to_push().push_type(PNPushType.APNS2).channels(channels).device_id(APNS2_DEVICE) \
        .topic(TOPIC).environment(PNPushEnvironment.DEVELOPMENT).future()


async def clear(pubnub):
    """Remove the test tokens on every gateway and environment so that nothing outlives the run."""
    for push_type in (PNPushType.FCM, PNPushType.GCM):
        try:
            await pubnub.remove_device_from_push().push_type(push_type).device_id(fcm_device()).future()
        except Exception as e:  # cleanup must never hide the real failure
            print('cleanup: could not clear a gateway (' + type(e).__name__ + ')')
    for push_type in (PNPushType.APNS, PNPushType.APNS2):
        for environment in (PNPushEnvironment.DEVELOPMENT, PNPushEnvironment.PRODUCTION):
            try:
                await pubnub.remove_device_from_push().push_type(push_type).device_id(APNS2_DEVICE) \
                    .topic(TOPIC).environment(environment).future()
            except Exception as e:
                print('cleanup: could not clear a gateway (' + type(e).__name__ + ')')


async def expect(pubnub, fcm, apns2, what):
    async def fcm_state():
        a.eq(await registered(pubnub, PNPushType.FCM), fcm, 'fcm ' + what)

    async def apns2_state():
        a.eq(await registered(pubnub, PNPushType.APNS2), apns2, 'apns2 ' + what)
    await aeventually(fcm_state)
    await aeventually(apns2_state)


@step('add_channels_to_push_builder', 'add_channels_to_push_kwargs', role='open')
async def test_add_channels_to_push(aclients):
    pubnub = aclients.asyncio('open', 'push_registrar')
    try:
        a.ok(len(APNS2_DEVICE) == 64 and set(APNS2_DEVICE) <= set('0123456789abcdef'), 'apns2 token is 64 hex chars')

        # snippet.add_channels_to_push_builder
        # for FCM
        envelope = await pubnub.add_channels_to_push() \
            .push_type(PNPushType.FCM) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id("deviceId") \
            .future()

        # for APNS2
        envelope = await pubnub.add_channels_to_push() \
            .push_type(PNPushType.APNS2) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id(APNS2_DEVICE) \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .future()

        if envelope.status.is_error():
            print("Error adding device to channels for push notifications")
        else:
            print("Device added to channels successfully")
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        await expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after add (builder)')
        await clear(pubnub)
        await expect(pubnub, [], [], 'after clearing')

        # snippet.add_channels_to_push_kwargs
        kwargs = {
            "push_type": PNPushType.FCM,
            "channels": ["ch1", "ch2", "ch3"],
            "device_id": "deviceId",
        }
        envelope = await pubnub.add_channels_to_push(**kwargs).future()

        kwargs = {
            "push_type": PNPushType.APNS2,
            "channels": ["ch1", "ch2", "ch3"],
            "device_id": APNS2_DEVICE,
            "topic": "myapptopic",
            "environment": PNPushEnvironment.DEVELOPMENT,
        }
        envelope = await pubnub.add_channels_to_push(**kwargs).future()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        await expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after add (keyword arguments)')
    finally:
        await clear(pubnub)


@step('list_push_channels_builder', role='open')
async def test_list_push_channels(aclients):
    pubnub = aclients.asyncio('open', 'push_lister')
    try:
        await seed(pubnub, CHANNELS)
        await expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding')

        # snippet.list_push_channels_builder
        # for FCM
        envelope = await pubnub.list_push_channels() \
            .push_type(PNPushType.FCM) \
            .device_id("deviceId") \
            .future()
        fcm_channels = envelope.result.channels

        # for APNS2
        envelope = await pubnub.list_push_channels() \
            .push_type(PNPushType.APNS2) \
            .device_id(APNS2_DEVICE) \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .future()
        apns2_channels = envelope.result.channels
        # snippet.end
        a.eq(sorted(fcm_channels), suffixed(CHANNELS), 'fcm channels listed')
        a.eq(sorted(apns2_channels), suffixed(CHANNELS), 'apns2 channels listed')
        a.ok(not envelope.status.is_error(), 'status is not an error')
        other = await pubnub.list_push_channels().push_type(PNPushType.FCM) \
            .device_id(names.with_suffix('unknown')).future()
        a.eq(other.result.channels, [], 'unknown device')
    finally:
        await clear(pubnub)


@step('remove_channels_from_push_builder', role='open')
async def test_remove_channels_from_push(aclients):
    pubnub = aclients.asyncio('open', 'push_remover')
    keep = 'keep_me'
    try:
        await seed(pubnub, CHANNELS + [keep])
        await expect(pubnub, suffixed(CHANNELS + [keep]), suffixed(CHANNELS + [keep]), 'after seeding')

        # snippet.remove_channels_from_push_builder
        # for FCM
        envelope = await pubnub.remove_channels_from_push() \
            .push_type(PNPushType.FCM) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id("deviceId") \
            .future()

        # for APNS2
        envelope = await pubnub.remove_channels_from_push() \
            .push_type(PNPushType.APNS2) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id(APNS2_DEVICE) \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .future()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        await expect(pubnub, suffixed([keep]), suffixed([keep]), 'after remove, only the other channel is left')
    finally:
        await clear(pubnub)


@step('remove_device_from_push_builder', role='open')
async def test_remove_device_from_push(aclients):
    pubnub = aclients.asyncio('open', 'push_device_remover')
    try:
        await seed(pubnub, CHANNELS)
        await expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding')

        # snippet.remove_device_from_push_builder
        # for FCM
        envelope = await pubnub.remove_device_from_push() \
            .push_type(PNPushType.FCM) \
            .device_id("deviceId") \
            .future()

        # for APNS2
        envelope = await pubnub.remove_device_from_push() \
            .push_type(PNPushType.APNS2) \
            .device_id(APNS2_DEVICE) \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .future()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        await expect(pubnub, [], [], 'after remove all')
    finally:
        await clear(pubnub)
