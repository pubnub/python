import tornado.ioloop
import tornado.web
import tornado.gen
import sys
import os

from pubnub.callbacks import SubscribeCallback
from pubnub.exceptions import PubNubException

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PUBNUB_ROOT)

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado, PubNubTornadoException

pnconf = PNConfiguration()
pnconf.subscribe_key = "demo"
pnconf.publish_key = "demo"

pubnub = PubNubTornado(pnconf)


class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("index.html")


class AsyncHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        pubnub.publish().channel("my_channel").message("hello").future().add_done_callback(self.callback)

    def callback(self, future):
        if future.exception() is not None:
            self.set_status(404)
            self.write("Something went wrong:" + str(future.exception()))
        else:
            envelope = future.result()
            self.write("success/")
            self.write(str(envelope.status.original_response))

        self.finish()


class YieldHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        try:
            envelope = yield pubnub.publish().channel("my_channel").message("hello").future()
            self.write(str(envelope.status.original_response))
        except PubNubTornadoException as e:
            self.write(str(e))


class Subscription(SubscribeCallback):
    @tornado.gen.coroutine
    def status(self, pubnub, status):
        print('# satus', str(status))
        try:
            yield pubnub.publish().channel("my_channel").message("hey").future()
        except Exception as e:
            print("failed to publish" + str(e))

    def presence(self, pubnub, presence):
        print('# presence')

    def message(self, pubnub, result):
        print('# message', result.message)


class StopHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        try:
            pubnub.stop()
        except PubNubException as e:
            self.write(str(e))


class SubscribeHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        pubnub.add_listener(Subscription())

        try:
            pubnub.subscribe().channels("my_channel").execute()
        except PubNubException as e:
            self.write(str(e))


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/publish_callback", AsyncHandler),
        (r"/publish_yield", YieldHandler),
        (r"/subscribe", SubscribeHandler),
        (r"/unsubscribe", StopHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
