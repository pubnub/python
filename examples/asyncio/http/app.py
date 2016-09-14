import asyncio
import json

import sys
import os

import aiohttp_cors as aiohttp_cors
from aiohttp import web

from pubnub import utils
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pubnub_asyncio import PubNubAsyncio

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
APP_ROOT = d(os.path.abspath(__file__))
sys.path.append(PUBNUB_ROOT)


from pubnub.exceptions import PubNubException
from pubnub.pnconfiguration import PNConfiguration

pnconf = PNConfiguration()
pnconf.subscribe_key = "sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe"
pnconf.publish_key = "pub-c-739aa0fc-3ed5-472b-af26-aca1b333ec52"
pnconf.uuid = "pubnub-demo-api-python-backend"
DEFAULT_CHANNEL = "pubnub_demo_api_python_channel"
EVENTS_CHANNEL = "pubnub_demo_api_python_events"
APP_KEY = utils.uuid()

loop = asyncio.get_event_loop()
pubnub = PubNubAsyncio(pnconf)


def publish_sync():
    return _not_implemented_error({
        "error": "Sync publish not implemented"
    })


def app_key_handler():
    return _ok({
        'app_key': APP_KEY
    })


def list_channels_handler():
    return _ok({
        "subscribed_channels": pubnub.get_subscribed_channels()
    })


def add_channel_handler(request):
    channel = request.GET['channel']

    if channel is None:
        return _internal_server_error({
            "error": "Channel missing"
        })

    try:
        pubnub.subscribe().channels(channel).execute()
        return _ok({
            "subscribed_channels": pubnub.get_subscribed_channels()
        })
    except PubNubException as e:
        return _internal_server_error({
            "message": str(e)
        })


def remove_channel_handler(request):
    channel = request.GET['channel']

    if channel is None:
        return _internal_server_error({
            "error": "Channel missing"
        })

    try:
        pubnub.unsubscribe().channels(channel).execute()
        return _ok({
            "subscribed_channels": pubnub.get_subscribed_channels()
        })
    except PubNubException as e:
        return _internal_server_error({
            "message": str(e)
        })


def _ok(body):
    return _prepare_response(body)


def _not_implemented_error(body):
    return web.HTTPNotImplemented(body=json.dumps(body).encode('utf-8'), content_type='application/json')


def _internal_server_error(body):
    return web.HTTPInternalServerError(body=json.dumps(body).encode('utf-8'), content_type='application/json')


def _prepare_response(body):
    return web.Response(body=json.dumps(body).encode('utf-8'), content_type='application/json')


def init_events_transmitter():
    """
    Method transmits status events to the specific channel
    :return:
    """
    class StatusListener(SubscribeCallback):
        def status(self, pubnub, status):
            event = "unknown"

            if status.operation == PNOperationType.PNSubscribeOperation \
                    and status.category == PNStatusCategory.PNConnectedCategory:
                event = "Connect"
            elif status.operation == PNOperationType.PNUnsubscribeOperation \
                    and status.category == PNStatusCategory.PNAcknowledgmentCategory:
                event = "Unsubscribe"

            asyncio.ensure_future(pubnub.publish().channel('status-' + APP_KEY).message({
                "event": event
            }).future(), loop=loop)

        def presence(self, pubnub, presence):
            pass

        def message(self, pubnub, message):
            pass

    listener = StatusListener()
    pubnub.add_listener(listener)


async def make_app(loop):
    app = web.Application()
    # (r"/listen", ListenHandler),

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    app.router.add_route('GET', '/app_key', app_key_handler)
    app.router.add_route('GET', '/subscription/add', add_channel_handler)
    app.router.add_route('GET', '/subscription/remove', remove_channel_handler)
    app.router.add_route('GET', '/subscription/list', list_channels_handler)
    app.router.add_route('GET', '/publish/sync', publish_sync)
    app.router.add_route('GET', '/publish/async', publish_sync)
    app.router.add_route('GET', '/publish/async2', publish_sync)

    for route in list(app.router.routes()):
        cors.add(route)

    srv = await loop.create_server(app.make_handler(), '0.0.0.0', 8080)
    return srv


if __name__ == "__main__":
    init_events_transmitter()
    loop.run_until_complete(make_app(loop))
    loop.run_forever()
