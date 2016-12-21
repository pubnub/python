import time
import tornado

from tornado import web
from tornado import gen

# pn.set_stream_logger('pubnub', logging.DEBUG)

ioloop = tornado.ioloop.IOLoop.current()


class SubscribeHandler(web.RequestHandler):
    def timestamp(self):
        return int(time.time() * 10000000)

    @gen.coroutine
    def get(self):
        tt = self.get_argument('tt')

        if tt is None:
            raise gen.Return(self.send_error(500, message={
                "error": "Channel missing"
            }))

        tt = int(tt)

        if tt > 0:
            yield gen.sleep(5000)

        self.write('{"t":{"t":"%d","r":12},"m":[]}' % self.timestamp())


class HeartbeatHandler(web.RequestHandler):
    def timestamp(self):
        return int(time.time() * 10000000)

    @gen.coroutine
    def get(self):
        self.write('{"status": 200, "message": "OK", "service": "Presence"}')


class TimeHandler(web.RequestHandler):
    def timestamp(self):
        return int(time.time() * 10000000)

    @gen.coroutine
    def get(self):
        self.write('[%d]' % self.timestamp())


def main():
    app = web.Application(
        [
            (r"/v2/subscribe/demo/my_channel/0", SubscribeHandler),
            (r"/v2/presence/sub-key/demo/channel/my_channel/heartbeat", HeartbeatHandler),
            (r"/time/0", TimeHandler),
        ],
        cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        xsrf_cookies=True,
    )
    app.listen(8089)
    ioloop.start()


if __name__ == "__main__":
    main()
