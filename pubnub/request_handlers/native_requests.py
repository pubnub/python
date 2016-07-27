import logging
import threading
import requests

from abc import abstractmethod, ABCMeta
from pubnub import utils
from pubnub.enums import PNStatusCategory
from pubnub.errors import PNERR_CLIENT_ERROR, PNERR_UNKNOWN_ERROR, PNERR_TOO_MANY_REDIRECTS_ERROR, PNERR_CLIENT_TIMEOUT, \
    PNERR_HTTP_ERROR, PNERR_CONNECTION_ERROR
from pubnub.errors import PNERR_SERVER_ERROR
from pubnub.exceptions import PubNubException
from pubnub.structures import RequestOptions, PlatformOptions, ResponseInfo

logger = logging.getLogger("pubnub")


class PubNubRequestHandler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def sync_request(self, platform_options, endpoint_call_options):
        pass


class RequestsHandler(PubNubRequestHandler):
    """ PubNub Python SDK Native requests handler based on `requests` HTTP library. """
    ENDPOINT_THREAD_COUNTER = 0

    def __init__(self):
        self.session = requests.Session()

    def sync_request(self, platform_options, endpoint_call_options):
        res = self.request(platform_options, endpoint_call_options)

        # http error
        if res.status_code != requests.codes.ok:
            if res.text is None:
                text = "N/A"
            else:
                text = res.text

            if res.status_code >= 500:
                err = PNERR_SERVER_ERROR
            else:
                err = PNERR_CLIENT_ERROR

            raise PubNubException(
                pn_error=err,
                errormsg=text,
                status_code=res.status_code
            )

        return res

    def async_request(self, endpoint_name, platform_options, endpoint_call_options, callback, cancellation_event):
        call = Call()

        def success_callback(res):
            status_category = PNStatusCategory.PNUnknownCategory
            response_info = None

            if res is not None:
                url = utils.urlparse(res.url)
                query = utils.parse_qs(url.query)
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

                callback(status_category, res.json(), response_info, PubNubException(
                    pn_error=err,
                    errormsg=text,
                    status_code=res.status_code
                ))
                call.executed_cb()
            else:
                callback(PNStatusCategory.PNAcknowledgmentCategory, res.json(), response_info, None)
                call.executed_cb()

        def error_callback(e):
            status_category = PNStatusCategory.PNBadRequestCategory
            # TODO: allow non PN errors

            if not type(e) is PubNubException:
                raise e

            if e._pn_error is PNERR_CONNECTION_ERROR:
                status_category = PNStatusCategory.PNUnexpectedDisconnectCategory
            elif e._pn_error is PNERR_CLIENT_TIMEOUT:
                status_category = PNStatusCategory.PNTimeoutCategory

            callback(status_category, None, None, e)
            call.executed_cb()

        def callback_to_invoke_in_another_thread():
            try:
                res = self.request(platform_options, endpoint_call_options)
                if cancellation_event is not None and cancellation_event.isSet():
                    # Since there are no way to affect on ongoing request it's response will be just ignored on cancel call
                    return

                success_callback(res)
            except PubNubException as e:
                error_callback(e)
            except Exception as e:
                # TODO: log the exception
                # TODO: Should non-pubnub exception to be reraised?
                error_callback(PubNubException(
                    pn_error=PNERR_UNKNOWN_ERROR,
                    errormsg="Exception in request thread: %s" % str(e)
                ))

        client = AsyncHTTPClient(callback_to_invoke_in_another_thread)

        thread = threading.Thread(
            target=client.run,
            name="EndpointThread-%s-%d" % (endpoint_name, ++RequestsHandler.ENDPOINT_THREAD_COUNTER)
        )
        thread.setDaemon(True)
        thread.start()

        call.thread = thread
        call.cancellation_event = cancellation_event

        return call

    def request(self, p_options, e_options):
        assert isinstance(p_options, PlatformOptions)
        assert isinstance(e_options, RequestOptions)
        url = p_options.scheme_and_host + e_options.path

        args = {
            "method": e_options.method_string,
            'headers': p_options.headers,
            "url": url,
            'params': e_options.query_string,
            'timeout': (e_options.connect_timeout, e_options.request_timeout)
        }

        if e_options.is_post():
            args['data'] = e_options.data
            logger.debug("%s %s %s" % (
                e_options.method_string,
                utils.build_url(
                    p_options.scheme_and_host,
                    e_options.path,
                    e_options.query_string), e_options.data))
        else:
            logger.debug("%s %s" % (
                e_options.method_string,
                utils.build_url(
                    p_options.scheme_and_host,
                    e_options.path,
                    e_options.query_string)))

        # connection error
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
