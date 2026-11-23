"""Scenario data and helpers of the mobile-push page, shared by the sync and asyncio tests: literal resource names
(NAMES, read by the janitor through support/resources.py) and the helpers the tests call outside the snippet markers.
Coroutine twins of a sync helper carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from pubnub.enums import PNPushEnvironment, PNPushType

from support import assertions as a
from support.wait import eventually
from support.wait import aeventually
from support.resources import APNS2_DEVICE

NAMES = ['deviceId', 'unknown']


TOPIC = 'myapptopic'


CHANNELS = ['ch1', 'ch2', 'ch3']


def suffixed(channels):
    return sorted(c for c in channels)


def fcm_device():
    return 'deviceId'


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


async def registered_async(pubnub, push_type):
    """Channels the service holds for the device on one gateway."""
    if push_type == PNPushType.APNS2:
        envelope = await pubnub.list_push_channels().push_type(push_type).device_id(APNS2_DEVICE) \
            .topic(TOPIC).environment(PNPushEnvironment.DEVELOPMENT).future()
    else:
        envelope = await pubnub.list_push_channels().push_type(push_type).device_id(fcm_device()).future()
    return sorted(envelope.result.channels)


async def seed_async(pubnub, channels):
    channels = suffixed(channels)
    await pubnub.add_channels_to_push().push_type(PNPushType.FCM).channels(channels).device_id(fcm_device()).future()
    await pubnub.add_channels_to_push().push_type(PNPushType.APNS2).channels(channels).device_id(APNS2_DEVICE) \
        .topic(TOPIC).environment(PNPushEnvironment.DEVELOPMENT).future()


async def clear_async(pubnub):
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


async def expect_async(pubnub, fcm, apns2, what):
    async def fcm_state():
        a.eq(await registered_async(pubnub, PNPushType.FCM), fcm, 'fcm ' + what)

    async def apns2_state():
        a.eq(await registered_async(pubnub, PNPushType.APNS2), apns2, 'apns2 ' + what)
    await aeventually(fcm_state)
    await aeventually(apns2_state)
