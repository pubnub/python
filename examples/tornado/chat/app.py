import tornado.ioloop
import tornado.web
import sys
import os

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PUBNUB_ROOT)

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


class AsyncHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        pnconf = PNConfiguration()
        pnconf.subscribe_key = "demo"
        pnconf.publish_key = "demo"
        pubnub = PubNub(pnconf)

        pubnub.publish().channel("my_channel").message("hello").async(self.success, self.error)

    def success(self, response):
        self.write(str(response.envelope))
        self.finish()

    def error(self, error):
        self.write(str(error))
        self.finish()


def make_app():
    return tornado.web.Application([
        (r"/", AsyncHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
