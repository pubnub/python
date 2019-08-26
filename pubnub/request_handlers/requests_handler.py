import logging
import threading
import requests
import six
import json  # noqa # pylint: disable=W0611

from requests import Session
from requests.adapters import HTTPAdapter

from pubnub import utils
from pubnub.enums import PNStatusCategory
from pubnub.errors import PNERR_CLIENT_ERROR, PNERR_UNKNOWN_ERROR, PNERR_TOO_MANY_REDIRECTS_ERROR,\
    PNERR_CLIENT_TIMEOUT, PNERR_HTTP_ERROR, PNERR_CONNECTION_ERROR
from pubnub.errors import PNERR_SERVER_ERROR
from pubnub.exceptions import PubNubException
from pubnub.request_handlers.base import BaseRequestHandler
from pubnub.structures import RequestOptions, PlatformOptions, ResponseInfo, Envelope

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


logger = logging.getLogger("pubnub")


class RequestsRequestHandler(BaseRequestHandler):
    """ PubNub Python SDK Native requests handler based on `requests` HTTP library. """
    ENDPOINT_THREAD_COUNTER = 0

    def __init__(self, pubnub):
        self.session = Session()

        self.session.mount('http://ps.pndsn.com', HTTPAdapter(max_retries=1, pool_maxsize=500))
        self.session.mount('https://ps.pndsn.com', HTTPAdapter(max_retries=1, pool_maxsize=500))
        self.session.mount('http://ps.pndsn.com/v2/subscribe', HTTPAdapter(pool_maxsize=500))
        self.session.mount('https://ps.pndsn.com/v2/subscribe', HTTPAdapter(pool_maxsize=500))

        self.pubnub = pubnub

    def sync_request(self, platform_options, endpoint_call_options):
        return self._build_envelope(platform_options, endpoint_call_options)

    def async_request(self, endpoint_name, platform_options, endpoint_call_options, callback, cancellation_event):
        call = Call()

        if cancellation_event is None:
            cancellation_event = threading.Event()

        def callback_to_invoke_in_another_thread():
            try:
                envelope = self._build_envelope(platform_options, endpoint_call_options)
                if cancellation_event is not None and cancellation_event.isSet():
                    # Since there are no way to affect on ongoing request it's response will
                    # be just ignored on cancel call
                    return

                callback(envelope)
            except PubNubException as e:
                logger.error("Async request PubNubException. %s" % str(e))
                callback(Envelope(
                    result=None,
                    status=endpoint_call_options.create_status(
                        category=PNStatusCategory.PNBadRequestCategory,
                        response=None,
                        response_info=None,
                        exception=e)))
            except Exception as e:
                logger.error("Async request Exception. %s" % str(e))
                callback(Envelope(
                    result=None,
                    status=endpoint_call_options.create_status(
                        category=PNStatusCategory.PNInternalExceptionCategory,
                        response=None,
                        response_info=None,
                        exception=e)))
            finally:
                call.executed_cb()

        client = AsyncHTTPClient(callback_to_invoke_in_another_thread)

        thread = threading.Thread(
            target=client.run,
            name="EndpointThread-%s-%d" % (endpoint_name, ++RequestsRequestHandler.ENDPOINT_THREAD_COUNTER)
        )
        thread.setDaemon(self.pubnub.config.daemon)
        thread.start()

        call.thread = thread
        call.cancellation_event = cancellation_event

        return call

    def _build_envelope(self, p_options, e_options):
        """ A wrapper for _invoke_url to separate request logic """

        status_category = PNStatusCategory.PNUnknownCategory
        response_info = None

        try:
            res = self._invoke_request(p_options, e_options, self.pubnub.base_origin)
        except PubNubException as e:
            if e._pn_error is PNERR_CONNECTION_ERROR:
                status_category = PNStatusCategory.PNUnexpectedDisconnectCategory
            elif e._pn_error is PNERR_CLIENT_TIMEOUT:
                status_category = PNStatusCategory.PNTimeoutCategory

            return Envelope(
                result=None,
                status=e_options.create_status(
                    category=status_category,
                    response=None,
                    response_info=response_info,
                    exception=e))

        if res is not None:
            url = six.moves.urllib.parse.urlparse(res.url)
            query = six.moves.urllib.parse.parse_qs(url.query)
            uuid = None
            auth_key = None

            if 'uuid' in query and len(query['uuid']) > 0:
                uuid = query['uuid'][0]

            if 'auth_key' in query and len(query['auth_key']) > 0:
                auth_key = query['auth_key'][0]

            response_info = ResponseInfo(
                status_code=res.status_code,
                tls_enabled='https' == url.scheme,
                origin=url.hostname,
                uuid=uuid,
                auth_key=auth_key,
                client_request=res.request
            )

        if res.status_code != requests.codes.ok:
            if res.status_code == 403:
                status_category = PNStatusCategory.PNAccessDeniedCategory

            if res.status_code == 400:
                status_category = PNStatusCategory.PNBadRequestCategory

            if res.text is None:
                text = "N/A"
            else:
                text = res.text

            if res.status_code >= 500:
                err = PNERR_SERVER_ERROR
            else:
                err = PNERR_CLIENT_ERROR
            try:
                response = res.json()
            except JSONDecodeError:
                response = None
            return Envelope(
                result=None,
                status=e_options.create_status(
                    category=status_category,
                    response=response,
                    response_info=response_info,
                    exception=PubNubException(
                        pn_error=err,
                        errormsg=text,
                        status_code=res.status_code
                    )))
        else:
            return Envelope(
                result=e_options.create_response(res.json()),
                status=e_options.create_status(
                    category=PNStatusCategory.PNAcknowledgmentCategory,
                    response=res.json(),
                    response_info=response_info,
                    exception=None))

    def _invoke_request(self, p_options, e_options, base_origin):
        assert isinstance(p_options, PlatformOptions)
        assert isinstance(e_options, RequestOptions)

        url = p_options.pn_config.scheme() + "://" + base_origin + e_options.path

        args = {
            "method": e_options.method_string,
            'headers': p_options.headers,
            "url": url,
            'params': e_options.query_string,
            'timeout': (e_options.connect_timeout, e_options.request_timeout)
        }

        if e_options.is_post() or e_options.is_patch():
            args['data'] = e_options.data
            logger.debug("%s %s %s" % (
                e_options.method_string,
                utils.build_url(
                    p_options.pn_config.scheme(),
                    base_origin,
                    e_options.path,
                    e_options.query_string), e_options.data))
        else:
            logger.debug("%s %s" % (
                e_options.method_string,
                utils.build_url(
                    p_options.pn_config.scheme(),
                    base_origin,
                    e_options.path,
                    e_options.query_string)))

        try:
            res = self.session.request(**args)
            logger.debug("GOT %s" % res.text)
        except requests.exceptions.ConnectionError as e:
            raise PubNubException(
                pn_error=PNERR_CONNECTION_ERROR,
                errormsg=str(e)
            )
        except requests.exceptions.HTTPError as e:
            raise PubNubException(
                pn_error=PNERR_HTTP_ERROR,
                errormsg=str(e)
            )
        except requests.exceptions.Timeout as e:
            raise PubNubException(
                pn_error=PNERR_CLIENT_TIMEOUT,
                errormsg=str(e)
            )
        except requests.exceptions.TooManyRedirects as e:
            raise PubNubException(
                pn_error=PNERR_TOO_MANY_REDIRECTS_ERROR,
                errormsg=str(e)
            )
        except Exception as e:
            raise PubNubException(
                pn_error=PNERR_UNKNOWN_ERROR,
                errormsg=str(e)
            )

        return res


class AsyncHTTPClient:
    """A wrapper for threaded calls"""

    def __init__(self, callback_to_invoke):
        self._callback_to_invoke = callback_to_invoke

    def run(self):
        self._callback_to_invoke()


class Call(object):
    """
    A platform dependent representation of async PubNub method call
    """

    def __init__(self):
        self.thread = None
        self.cancellation_event = None
        self.is_executed = False
        self.is_canceled = False

    def cancel(self):
        """
        Set Event flag to stop thread on timeout. This will not stop thread immediately, it will stopped
          only after ongoing request will be finished
        :return: nothing
        """
        if self.cancellation_event is not None:
            self.cancellation_event.set()
        self.is_canceled = True

    def join(self):
        if isinstance(self.thread, threading.Thread):
            self.thread.join()

    def executed_cb(self):
        self.is_executed = True
