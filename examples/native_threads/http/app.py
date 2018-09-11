import logging
import os
import sys
import time

from flask import Flask, jsonify
from flask import request

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PUBNUB_ROOT)

import pubnub as pn
from pubnub import utils
from pubnub.exceptions import PubNubException
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


pn.set_stream_logger('pubnub', logging.DEBUG)
logger = logging.getLogger("myapp")

app = Flask(__name__)

pnconfig = PNConfiguration()
pnconfig.subscribe_request_timeout = 10
pnconfig.subscribe_key = "sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe"
pnconfig.publish_key = "pub-c-739aa0fc-3ed5-472b-af26-aca1b333ec52"
pnconfig.uuid = "pubnub-demo-api-python-backend"
DEFAULT_CHANNEL = "pubnub_demo_api_python_channel"
EVENTS_CHANNEL = "pubnub_demo_api_python_events"
APP_KEY = utils.uuid()

pubnub = PubNub(pnconfig)
logger.info("SDK Version: %s", pubnub.SDK_VERSION)


@app.route("/app_key")
def app_key():
    return {
        'app_key': APP_KEY
    }


@app.route("/subscription/add")
def subscription_add():
    channel = request.args.get('channel')

    if channel is None:
        return jsonify({
            "error": "Channel missing"
        }), 500

    pubnub.subscribe().channels(channel).execute()
    return jsonify({
        'subscribed_channels': pubnub.get_subscribed_channels()
    })


@app.route("/subscription/remove")
def subscription_remove():
    channel = request.args.get('channel')

    if channel is None:
        return jsonify({
            "error": "Channel missing"
        }), 500

    pubnub.unsubscribe().channels(channel).execute()

    return jsonify({
        'subscribed_channels': pubnub.get_subscribed_channels()
    })


@app.route("/subscription/list")
def subscription_list():
    return jsonify({
        'subscribed_channels': pubnub.get_subscribed_channels()
    })


@app.route('/publish/sync')
def publish_sync():
    channel = request.args.get('channel')

    if channel is None:
        return jsonify({
            "error": "Channel missing"
        }), 500

    try:
        envelope = pubnub.publish().channel(channel).message("hello from yield-based publish").sync()
        return jsonify({
            "original_response": str(envelope.status.original_response)
        })
    except PubNubException as e:
        return jsonify({
            "message": str(e)
        }), 500


@app.route('/publish/async')
def publish_async():
    channel = request.args.get('channel')

    if channel is None:
        return jsonify({
            "error": "Channel missing"
        }), 500

    def stub(res, state):
        pass

    pubnub.publish().channel(channel).message("hello from yield-based publish")\
        .pn_async(stub)

    return jsonify({
        "message": "Publish task scheduled"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0')
    time.sleep(100)
