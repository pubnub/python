import tornado.ioloop
import tornado.web
import tornado.gen
import sys
import os

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PUBNUB_ROOT)


from pubnub.pubnub_tornado import SubscribeListener
from pubnub.exceptions import PubNubException
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado, PubNubTornadoException


pnconf = PNConfiguration()
pnconf.subscribe_key = "demo"
pnconf.publish_key = "demo"
channel = "my_channel"

pubnub = PubNubTornado(pnconf)


class MainHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.web.asynchronous
    def get(self):
        self.render("index.html")


class AsyncHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.web.asynchronous
    def get(self):
        pubnub.publish().channel(channel).message("hello from callback-based publish")\
            .future().add_done_callback(self.callback)

    def callback(self, future):
        if future.exception() is not None:
            self.set_status(500)
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
            envelope = yield pubnub.publish().channel(channel).message("hello from yield-based publish").future()
            self.write(str(envelope.status.original_response))
        except PubNubTornadoException as e:
            self.set_status(500)
            self.write(str(e))


class UnsubscribeHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self):
        listener = SubscribeListener()
        pubnub.add_listener(listener)

        try:
            pubnub.unsubscribe().channels(channel).execute()
            yield listener.wait_for_disconnect()
            self.write("unsubscribed from %s" % channel)
        except PubNubException as e:
            self.write(str(e))


class SubscribeHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self):
        listener = SubscribeListener()
        pubnub.add_listener(listener)

        try:
            pubnub.subscribe().channels(channel).execute()
            yield listener.wait_for_connect()
            res = yield listener.wait_for_message_on(channel)
            pubnub.unsubscribe().channels(channel).execute()
            yield listener.wait_for_disconnect()
            self.write(str(res.message))

        except PubNubException as e:
            self.write(str(e))


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/publish_callback", AsyncHandler),
        (r"/publish_yield", YieldHandler),
        (r"/subscribe", SubscribeHandler),
        (r"/unsubscribe", UnsubscribeHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
