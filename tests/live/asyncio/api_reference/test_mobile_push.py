"""Docs page: mobile push (asyncio). Source: docs/sdks/asyncio/api-reference/mobile-push.md.

Only the registration side is testable. A push is delivered by FCM or APNs to a real device, so delivery is not tested.
The device tokens are made up and fixed (support/resources.py PUSH_DEVICES), and every gateway is cleaned in a finally
block and by the janitor.
"""
from support import assertions as a
from shared.mobile_push import (
    APNS2_DEVICE, CHANNELS, clear_async as clear, expect_async as expect, seed_async as seed, suffixed,
)


async def test_add_channels_to_push_builder(aclients):
    """Snippets: add_channels_to_push_builder, add_channels_to_push_kwargs."""
    pubnub = aclients.asyncio('open', 'push_registrar')
    try:
        a.ok(len(APNS2_DEVICE) == 64 and set(APNS2_DEVICE) <= set('0123456789abcdef'), 'apns2 token is 64 hex chars')

        # snippet.add_channels_to_push_builder
        from pubnub.enums import PNPushEnvironment, PNPushType

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
            .device_id("5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a") \
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
        from pubnub.enums import PNPushEnvironment, PNPushType

        kwargs = {
            "push_type": PNPushType.FCM,
            "channels": ["ch1", "ch2", "ch3"],
            "device_id": "deviceId",
        }
        envelope = await pubnub.add_channels_to_push(**kwargs).future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")

        kwargs = {
            "push_type": PNPushType.APNS2,
            "channels": ["ch1", "ch2", "ch3"],
            "device_id": "5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a",
            "topic": "myapptopic",
            "environment": PNPushEnvironment.DEVELOPMENT,
        }
        envelope = await pubnub.add_channels_to_push(**kwargs).future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        await expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after add (keyword arguments)')
    finally:
        await clear(pubnub)


async def test_list_push_channels_builder(aclients):
    """Snippet: list_push_channels_builder."""
    pubnub = aclients.asyncio('open', 'push_lister')
    try:
        await seed(pubnub, CHANNELS)
        await expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding')

        # snippet.list_push_channels_builder
        from pubnub.enums import PNPushEnvironment, PNPushType

        # for FCM
        envelope = await pubnub.list_push_channels() \
            .push_type(PNPushType.FCM) \
            .device_id("deviceId") \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        else:
            fcm_channels = envelope.result.channels

        # for APNS2
        envelope = await pubnub.list_push_channels() \
            .push_type(PNPushType.APNS2) \
            .device_id("5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a") \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        else:
            apns2_channels = envelope.result.channels
        # snippet.end
        a.eq(sorted(fcm_channels), suffixed(CHANNELS), 'fcm channels listed')
        a.eq(sorted(apns2_channels), suffixed(CHANNELS), 'apns2 channels listed')
        a.ok(not envelope.status.is_error(), 'status is not an error')
        other = await pubnub.list_push_channels().push_type(PNPushType.FCM) \
            .device_id('unknown').future()
        a.eq(other.result.channels, [], 'unknown device')
    finally:
        await clear(pubnub)


async def test_remove_channels_from_push_builder(aclients):
    """Snippet: remove_channels_from_push_builder."""
    pubnub = aclients.asyncio('open', 'push_remover')
    keep = 'keep_me'
    try:
        await seed(pubnub, CHANNELS + [keep])
        await expect(pubnub, suffixed(CHANNELS + [keep]), suffixed(CHANNELS + [keep]), 'after seeding')

        # snippet.remove_channels_from_push_builder
        from pubnub.enums import PNPushEnvironment, PNPushType

        # for FCM
        envelope = await pubnub.remove_channels_from_push() \
            .push_type(PNPushType.FCM) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id("deviceId") \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")

        # for APNS2
        envelope = await pubnub.remove_channels_from_push() \
            .push_type(PNPushType.APNS2) \
            .channels(["ch1", "ch2", "ch3"]) \
            .device_id("5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a") \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        await expect(pubnub, suffixed([keep]), suffixed([keep]), 'after remove, only the other channel is left')
    finally:
        await clear(pubnub)


async def test_remove_device_from_push_builder(aclients):
    """Snippet: remove_device_from_push_builder."""
    pubnub = aclients.asyncio('open', 'push_device_remover')
    try:
        await seed(pubnub, CHANNELS)
        await expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding')

        # snippet.remove_device_from_push_builder
        from pubnub.enums import PNPushEnvironment, PNPushType

        # for FCM
        envelope = await pubnub.remove_device_from_push() \
            .push_type(PNPushType.FCM) \
            .device_id("deviceId") \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")

        # for APNS2
        envelope = await pubnub.remove_device_from_push() \
            .push_type(PNPushType.APNS2) \
            .device_id("5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a") \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        await expect(pubnub, [], [], 'after remove all')
    finally:
        await clear(pubnub)
