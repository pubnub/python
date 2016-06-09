import json
import logging
import time

import datetime

from . import utils
from .callbacks import SubscribeCallback
from .models.server.subscribe import SubscribeEnvelope
from .workers import SubscribeMessageWorker
from .endpoints.pubsub.subscribe import Subscribe
from .models.consumer.common import PNStatus
from .dtos import SubscribeOperation, UnsubscribeOperation
from .managers import StateManager, ListenerManager, SubscriptionManager
from .builders import SubscribeBuilder
from .enums import PNStatusCategory
from .structures import ResponseInfo
from .exceptions import PubNubException
from .errors import PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_JSON_DECODING_FAILED
from .pubnub_core import PubNubCore

import tornado.httpclient
import tornado.ioloop
from tornado.concurrent import Future
from tornado.queues import Queue
from tornado.locks import Event
from tornado import ioloop
from tornado import gen

# default_ioloop = tornado.ioloop.IOLoop.instance()
logger = logging.getLogger("pubnub")


class PubNubTornado(PubNubCore):
    def stop(self):
        self.ioloop.stop()

    def start(self):
        self.ioloop.start()

    def timeout(self, delay, callback, *args):
        handle = None

        def cancel():
            self.ioloop.remove_timeout(handle)

        def cb():
            if callback is not None:
                callback(*args)

        handle = self.ioloop.add_timeout(time.time() + float(delay), cb)

        return cancel

    # TODO: deprecate
    def set_ioloop(self, ioloop):
        self.ioloop = ioloop

    def sdk_platform(self):
        return "-Tornado"

    def __init__(self, config, custom_ioloop=None):
        super(PubNubTornado, self).__init__(config)
        self.ioloop = custom_ioloop or ioloop.IOLoop.instance()

        self._subscription_manager = TornadoSubscriptionManager(self)

        # TODO: choose a correct client here http://www.tornadoweb.org/en/stable/httpclient.html
        # TODO: 1000?
        self.http = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
        self.id = None
        # TODO: add accept encoding should be configurable
        self.headers = {
            'User-Agent': self.sdk_name,
            'Accept-Encoding': 'utf-8'
        }

    def add_listener(self, listener):
        if self._subscription_manager is not None:
            self._subscription_manager.add_listener(listener)
        else:
            raise Exception("Subscription manager is not enabled for this instance")

    def subscribe(self):
        return SubscribeBuilder(self._subscription_manager)

    def unsubscribe(self):
        pass

    def request_sync(self, *args):
        raise NotImplementedError

    def request_async(self, *args):
        raise NotImplementedError

    def request_deferred(self, *args):
        raise NotImplementedError

    def request_future(self, options_func, create_response, create_status_response):
        options = options_func()
        future = Future()

        url = utils.build_url(self.config.scheme(), self.config.origin,
                              options.path, options.query_string)
        logger.debug("%s %s %s" % (options.method_string, url, options.data))

        request = tornado.httpclient.HTTPRequest(
            url=url,
            method=options.method_string,
            headers=self.headers,
            body=options.data if options.data is not None else None,
            connect_timeout=self.config.connect_timeout,
            request_timeout=self.config.non_subscribe_request_timeout)

        def response_callback(response):
            body = response.body
            response_info = None
            status_category = PNStatusCategory.PNUnknownCategory

            if response is not None:
                request_url = utils.urlparse(response.effective_url)
                query = utils.parse_qs(request_url.query)
                uuid = None
                auth_key = None

                if 'uuid' in query and len(query['uuid']) > 0:
                    uuid = query['uuid'][0]

                if 'auth_key' in query and len(query['auth_key']) > 0:
                    auth_key = query['auth_key'][0]

                response_info = ResponseInfo(
                    status_code=response.code,
                    tls_enabled='https' == request_url.scheme,
                    origin=request_url.hostname,
                    uuid=uuid,
                    auth_key=auth_key,
                    client_request=response.request
                )

            if body is not None and len(body) > 0:
                try:
                    data = json.loads(body)
                except TypeError:
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except ValueError:
                        tornado_result = TornadoEnvelope(
                            create_response(None),
                            create_status_response(status_category, response, response_info, PubNubException(
                                pn_error=PNERR_JSON_DECODING_FAILED,
                                errormsg='json decode error')
                                                   )
                        )
                        future.set_exception(tornado_result)
                        return
            else:
                data = "N/A"

            if response.error is not None:
                if response.code >= 500:
                    err = PNERR_SERVER_ERROR
                else:
                    err = PNERR_CLIENT_ERROR

                if response.code == 403:
                    status_category = PNStatusCategory.PNAccessDeniedCategory

                if response.code == 400:
                    status_category = PNStatusCategory.PNBadRequestCategory

                if response.code == 599:
                    status_category = PNStatusCategory.PNTimeoutCategory

                # TODO: return exception with stateinfo
                future.set_exception(PubNubTornadoException(
                    result=data,
                    status=create_status_response(status_category, data, response_info,
                                                  PubNubException(
                                                      errormsg=data,
                                                      pn_error=err,
                                                      status_code=response.code,
                                                  ))
                ))

                # future.set_exception(tornado_result)
            else:
                future.set_result(TornadoEnvelope(
                    result=create_response(data),
                    status=create_status_response(status_category, data, response_info, None)
                )
                )

        self.http.fetch(
            request=request,
            callback=response_callback
        )

        return future


class TornadoSubscribeMessageWorker(SubscribeMessageWorker):
    @tornado.gen.coroutine
    def run(self):
        yield self._take_message()

    @tornado.gen.coroutine
    def _take_message(self):
        i = 0
        while not self._event.is_set():
            try:
                msg = yield self._queue.get(datetime.timedelta(seconds=1))
                if msg is not None:
                    self._process_incoming_payload(msg)
                self._queue.task_done()
            except tornado.gen.TimeoutError:
                print("%d continue" % i)
                i += 1
                continue
            # TODO: should context of callback be changed?
            # except Exception as e:
            #     print("!!! ex")
            #     break


# TODO: inherit from managers.SubscriptionManager
class TornadoSubscriptionManager(SubscriptionManager):
    def __init__(self, pubnub_instance):
        self._message_queue = Queue()
        self._consumer_event = Event()
        super(TornadoSubscriptionManager, self).__init__(pubnub_instance)

    def _set_consumer_event(self):
        self._consumer_event.set()

    def _message_queue_put(self, message):
        self._message_queue.put(message)

    def _start_worker(self):
        self._consumer = TornadoSubscribeMessageWorker(self._pubnub, self._listener_manager,
                                                       self._message_queue, self._consumer_event)

        self._pubnub.ioloop.add_callback(self._consumer.run)

    @tornado.gen.coroutine
    def _start_subscribe_loop(self):
        self._stop_subscribe_loop()

        combined_channels = self._subscription_state.prepare_channel_list(True)
        combined_groups = self._subscription_state.prepare_channel_group_list(True)

        if len(combined_channels) == 0 and len(combined_groups) == 0:
            return

        try:
            envelope = yield Subscribe(self._pubnub) \
                .channels(combined_channels).groups(combined_groups) \
                .timetoken(self._timetoken).region(self._region) \
                .filter_expression(self._pubnub.config.filter_expression) \
                .future()
        except PubNubTornadoException as e:
            if e.status is not None and e.status.category == PNStatusCategory.PNTimeoutCategory:
                yield self._start_subscribe_loop()
            else:
                self._listener_manager.announce_status(e.status)

            return
        except Exception as e:
            print("!!! ex2", e)
            return

        self._handle_endpoint_call(envelope.result, envelope.status)


class TornadoEnvelope(object):
    def __init__(self, result, status):
        self.result = result
        self.status = status


class PubNubTornadoException(Exception):
    def __init__(self, result, status):
        self.result = result
        self.status = status

    def __str__(self):
        return str(self.status.error_data.exception)
