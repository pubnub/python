"""Docs page: mobile push (sync). Source: docs/sdks/python/api-reference/mobile-push.md.

Only the registration side is testable. A push is delivered by FCM or APNs to a real device, so delivery is not tested.
The device tokens are made up and fixed (support/resources.py PUSH_DEVICES), and every gateway is cleaned in a finally
block and by the janitor.
"""
from support import assertions as a
from shared.mobile_push import APNS2_DEVICE, CHANNELS, clear, expect, seed, suffixed


def test_add_channels_to_push_builder(clients):
    """Snippets: add_channels_to_push_builder, add_channels_to_push_named."""
    pubnub = clients.sync('open', 'push_registrar')
    try:
        a.ok(len(APNS2_DEVICE) == 64 and set(APNS2_DEVICE) <= set('0123456789abcdef'), 'apns2 token is 64 hex chars')

        # snippet.add_channels_to_push_builder
        from pubnub.enums import PNPushEnvironment, PNPushType

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
            .device_id("5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a") \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()
        # snippet.end
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after add (builder)')
        clear(pubnub)
        expect(pubnub, [], [], 'after clearing')

        # snippet.add_channels_to_push_named
        from pubnub.enums import PNPushEnvironment, PNPushType

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
            device_id="5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a",
            topic="myapptopic",
            environment=PNPushEnvironment.DEVELOPMENT
        ).sync()
        # snippet.end
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after add (named)')
    finally:
        clear(pubnub)


def test_list_push_channels_builder(clients):
    """Snippets: list_push_channels_builder, list_push_channels_named."""
    pubnub = clients.sync('open', 'push_lister')
    try:
        seed(pubnub, CHANNELS)
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding')

        # snippet.list_push_channels_builder
        from pubnub.enums import PNPushEnvironment, PNPushType

        # For FCM
        envelope = pubnub.list_push_channels() \
            .push_type(PNPushType.FCM) \
            .device_id("deviceId") \
            .sync()
        fcm_channels = envelope.result.channels

        # For APNS2
        envelope = pubnub.list_push_channels() \
            .push_type(PNPushType.APNS2) \
            .device_id("5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a") \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()
        apns2_channels = envelope.result.channels
        # snippet.end
        a.eq(sorted(fcm_channels), suffixed(CHANNELS), 'fcm channels listed')
        a.eq(sorted(apns2_channels), suffixed(CHANNELS), 'apns2 channels listed')
        a.ok(not envelope.status.is_error(), 'status is not an error')

        # snippet.list_push_channels_named
        from pubnub.enums import PNPushEnvironment, PNPushType

        # For FCM
        envelope = pubnub.list_push_channels(push_type=PNPushType.FCM, device_id="deviceId").sync()
        fcm_channels = envelope.result.channels

        # For APNS2
        envelope = pubnub.list_push_channels(
            push_type=PNPushType.APNS2,
            device_id="5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a",
            topic="myapptopic",
            environment=PNPushEnvironment.DEVELOPMENT
        ).sync()
        apns2_channels = envelope.result.channels
        # snippet.end
        a.eq(sorted(fcm_channels), suffixed(CHANNELS), 'fcm channels listed (named)')
        a.eq(sorted(apns2_channels), suffixed(CHANNELS), 'apns2 channels listed (named)')

        # A device nothing was registered for lists no channels
        other = pubnub.list_push_channels().push_type(PNPushType.FCM).device_id('unknown').sync()
        a.eq(other.result.channels, [], 'unknown device')
    finally:
        clear(pubnub)


def test_remove_channels_from_push_builder(clients):
    """Snippets: remove_channels_from_push_builder, remove_channels_from_push_named."""
    pubnub = clients.sync('open', 'push_remover')
    keep = 'keep_me'
    try:
        seed(pubnub, CHANNELS + [keep])
        expect(pubnub, suffixed(CHANNELS + [keep]), suffixed(CHANNELS + [keep]), 'after seeding')

        # snippet.remove_channels_from_push_builder
        from pubnub.enums import PNPushEnvironment, PNPushType

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
            .device_id("5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a") \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        expect(pubnub, suffixed([keep]), suffixed([keep]), 'after remove (builder), only the other channel is left')

        seed(pubnub, CHANNELS)
        expect(pubnub, suffixed(CHANNELS + [keep]), suffixed(CHANNELS + [keep]), 'after seeding again')

        # snippet.remove_channels_from_push_named
        from pubnub.enums import PNPushEnvironment, PNPushType

        # For FCM
        envelope = pubnub.remove_channels_from_push(channels=["ch1", "ch2", "ch3"],
                                                    push_type=PNPushType.FCM,
                                                    device_id="deviceId") \
            .sync()

        # For APNS2
        envelope = pubnub.remove_channels_from_push(
            channels=["ch1", "ch2", "ch3"],
            push_type=PNPushType.APNS2,
            device_id="5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a",
            topic="myapptopic",
            environment=PNPushEnvironment.DEVELOPMENT
        ).sync()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        expect(pubnub, suffixed([keep]), suffixed([keep]), 'after remove (named), only the other channel is left')
    finally:
        clear(pubnub)


def test_remove_device_from_push_builder(clients):
    """Snippets: remove_device_from_push_builder, remove_device_from_push_named."""
    pubnub = clients.sync('open', 'push_device_remover')
    try:
        seed(pubnub, CHANNELS)
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding')

        # snippet.remove_device_from_push_builder
        from pubnub.enums import PNPushEnvironment, PNPushType

        # For FCM
        envelope = pubnub.remove_device_from_push() \
            .push_type(PNPushType.FCM) \
            .device_id("deviceId") \
            .sync()

        # For APNS2
        envelope = pubnub.remove_device_from_push() \
            .push_type(PNPushType.APNS2) \
            .device_id("5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a") \
            .topic("myapptopic") \
            .environment(PNPushEnvironment.DEVELOPMENT) \
            .sync()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        expect(pubnub, [], [], 'after remove all (builder)')

        seed(pubnub, CHANNELS)
        expect(pubnub, suffixed(CHANNELS), suffixed(CHANNELS), 'after seeding again')

        # snippet.remove_device_from_push_named
        from pubnub.enums import PNPushEnvironment, PNPushType

        # For FCM
        envelope = pubnub.remove_device_from_push(device_id="deviceId", push_type=PNPushType.FCM).sync()

        # For APNS2
        envelope = pubnub.remove_device_from_push(
            device_id="5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a",
            push_type=PNPushType.APNS2,
            topic="myapptopic",
            environment=PNPushEnvironment.DEVELOPMENT
        ).sync()
        # snippet.end
        a.ok(not envelope.status.is_error(), 'status is not an error')
        expect(pubnub, [], [], 'after remove all (named)')
    finally:
        clear(pubnub)
