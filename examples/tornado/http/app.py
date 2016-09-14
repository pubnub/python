import json
import tornado.ioloop
import tornado.web
import tornado.gen
import sys
import os

from pubnub import utils
from pubnub.enums import PNStatusCategory, PNOperationType

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
APP_ROOT = d(os.path.abspath(__file__))
sys.path.append(PUBNUB_ROOT)


from pubnub.pubnub_tornado import SubscribeListener, TornadoEnvelope
from pubnub.exceptions import PubNubException
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado, PubNubTornadoException
from pubnub.pubnub_tornado import SubscribeCallback
from pubnub.models.consumer.pubsub import PNPublishResult

pnconf = PNConfiguration()
pnconf.subscribe_key = "sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe"
pnconf.publish_key = "pub-c-739aa0fc-3ed5-472b-af26-aca1b333ec52"
pnconf.uuid = "pubnub-demo-api-python-backend"
DEFAULT_CHANNEL = "pubnub_demo_api_python_channel"
EVENTS_CHANNEL = "pubnub_demo_api_python_events"
APP_KEY = utils.uuid()

pubnub = PubNubTornado(pnconf)


class SyncPublishHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        return self.send_error(501, message={
            "error": "Sync publish not implemented"
        })


class AsyncPublishHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        channel = self.get_argument('channel')
        if channel is None:
            return self.send_error(500, message={
                "error": "Channel missing"
            })

        try:
            envelope = yield pubnub.publish().channel(channel).message("hello from yield-based publish").future()
            self.write(json.dumps({
                "original_response": str(envelope.status.original_response)
            }))
        except PubNubTornadoException as e:
            self.send_error(500, message={
                "message": str(e)
            })


class AsyncPublishHandler2(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.web.asynchronous
    def get(self):
        channel = self.get_argument('channel')
        if channel is None:
            return self.send_error(500, message={
                "error": "Channel missing"
            })

        pubnub.publish().channel(channel).message("hello from callback-based publish")\
            .future().add_done_callback(self.callback)

    def callback(self, future):
        if future.exception() is not None:
            self.send_error(500, message={
                "message": str(str(future.exception()))
            })
        else:
            envelope = future.result()
            self.write(json.dumps({
                "original_response": str(envelope.status.original_response)
            }))

        self.finish()


class AppKeyHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'application/json')

        self.write(json.dumps({
            "app_key": APP_KEY
        }))


class ListenHandler(tornado.web.RequestHandler):
    """
    Long-polling request
    """
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'application/json')

        channel = self.get_argument('channel')
        if channel is None:
            return self.send_error(500, message={
                "error": "Channel missing"
            })

        listener = SubscribeListener()
        pubnub.add_listener(listener)

        try:
            res = yield listener.wait_for_message_on(channel)
            self.write(json.dumps({"message": res.message}))
        except PubNubException as e:
            self.send_error(500, message={
                "message": str(e)
            })
        finally:
            pubnub.remove_listener(listener)


class ListChannelHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'application/json')

        self.write(json.dumps({
            "subscribed_channels": pubnub.get_subscribed_channels()
        }))


class AddChannelHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'application/json')

        channel = self.get_argument('channel')
        if channel is None:
            return self.send_error(500, message={
                "error": "Channel missing"
            })

        try:
            pubnub.subscribe().channels(channel).execute()
            self.write(json.dumps({
                "subscribed_channels": pubnub.get_subscribed_channels()
            }))
        except PubNubException as e:
            self.send_error(500, message={
                "message": str(e)
            })


class RemoveChannelHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'application/json')

        channel = self.get_argument('channel')
        if channel is None:
            return self.send_error(500, message={
                "error": "Channel missing"
            })

        try:
            pubnub.unsubscribe().channels(channel).execute()
            self.write(json.dumps({
                "subscribed_channels": pubnub.get_subscribed_channels()
            }))
        except PubNubException as e:
            self.send_error(500, message={
                "message": str(e)
            })


def init_events_transmitter():
    """
    Method transmits status events to the specific channel
    :return:
    """
    class StatusListener(SubscribeCallback):
        def status(self, pubnub, status):
            def callback(future):
                envelope = future.result()
                assert isinstance(envelope, TornadoEnvelope)

                result = envelope.result
                assert isinstance(result, PNPublishResult)

                print(result)

            event = "unknown"

            if status.operation == PNOperationType.PNSubscribeOperation \
                    and status.category == PNStatusCategory.PNConnectedCategory:
                event = "Connect"
            elif status.operation == PNOperationType.PNUnsubscribeOperation \
                    and status.category == PNStatusCategory.PNAcknowledgmentCategory:
                event = "Unsubscribe"

            tornado.ioloop.IOLoop.current().add_future(
                pubnub.publish().channel('status-' + APP_KEY).message({
                    "event": event
                }).future(),
                callback
            )

        def presence(self, pubnub, presence):
            pass

        def message(self, pubnub, message):
            pass

    listener = StatusListener()
    pubnub.add_listener(listener)


def make_app():
    return tornado.web.Application([
        (r"/listen", ListenHandler),
        (r"/app_key", AppKeyHandler),
        (r"/publish/sync", SyncPublishHandler),
        (r"/publish/async", AsyncPublishHandler),
        (r"/publish/async2", AsyncPublishHandler2),
        (r"/subscription/list", ListChannelHandler),
        (r"/subscription/add", AddChannelHandler),
        (r"/subscription/remove", RemoveChannelHandler),
    ],
        static_path=os.path.join(APP_ROOT, "static"),
        template_path=os.path.join(APP_ROOT, "templates"),)


if __name__ == "__main__":
    init_events_transmitter()
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
