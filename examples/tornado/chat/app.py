import tornado.ioloop
import tornado.web
import tornado.gen
import sys
import os

from pubnub.exceptions import PubNubException

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PUBNUB_ROOT)

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado


class AsyncHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        pnconf = PNConfiguration()
        pnconf.subscribe_key = "demo"
        pnconf.publish_key = "demo"
        pubnub = PubNubTornado(pnconf)

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
        pnconf = PNConfiguration()
        pnconf.subscribe_key = "demo"
        pnconf.publish_key = "demo"
        pubnub = PubNubTornado(pnconf)

        try:
            envelope = yield pubnub.publish().channel("my_channel").message("hello").future()
            self.write(str(envelope.status.original_response))
        except PubNubException as e:
            self.write(str(e))


def make_app():
    return tornado.web.Application([
        (r"/publish_callback", AsyncHandler),
        (r"/publish_yield", YieldHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
