import tornado.ioloop
import tornado.web
import tornado.gen
import sys
import os

from tornado.stack_context import ExceptionStackContext

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

        pubnub.publish().channel("my_channel").message("hello").async(self.success, self.error)

    def success(self, response):
        self.write(str(response.envelope))
        self.finish()

    def error(self, error):
        self.write(str(error))
        self.finish()


# TODO: implement yielding pubnub result
class YieldHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        pnconf = PNConfiguration()
        pnconf.subscribe_key = "demo"
        pnconf.publish_key = "demo"
        pubnub = PubNubTornado(pnconf)

        def handle_err(type, second, third):
            self.write(str(type))

        with ExceptionStackContext(handle_err):
            response = yield pubnub.publish().channel("my_channel").message("hello").deferred()
            self.write(str(response))


def make_app():
    return tornado.web.Application([
        (r"/async", AsyncHandler),
        (r"/yield", YieldHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
