from asyncio import Event
import asyncio
import logging
import time
import httpx
import json  # noqa # pylint: disable=W0611
import urllib

from pubnub import utils
from pubnub.enums import PNOperationType, PNStatusCategory
from pubnub.errors import PNERR_CLIENT_ERROR, PNERR_JSON_DECODING_FAILED, PNERR_SERVER_ERROR
from pubnub.exceptions import PubNubException
from pubnub.models.envelopes import AsyncioEnvelope
from pubnub.request_handlers.base import BaseRequestHandler
from pubnub.structures import RequestOptions, ResponseInfo

logger = logging.getLogger("pubnub")


class PubNubAsyncHTTPTransport(httpx.AsyncHTTPTransport):
    is_closed = False

    def close(self):
        self.is_closed = True
        asyncio.create_task(super().aclose())


class AsyncHttpxRequestHandler(BaseRequestHandler):
    """ PubNub Python SDK asychronous requests handler based on the `httpx` HTTP library. """
    ENDPOINT_THREAD_COUNTER: int = 0
    _connector: httpx.AsyncHTTPTransport = None
    _session: httpx.AsyncClient = None

    def __init__(self, pubnub):
        self.pubnub = pubnub
        self._connector = PubNubAsyncHTTPTransport(verify=True, http2=True)

    async def create_session(self):
        self._session = httpx.AsyncClient(
            timeout=httpx.Timeout(self.pubnub.config.connect_timeout),
            transport=self._connector
        )

    async def close_session(self):
        if self._session is not None:
            self._connector.close()
            await self._session.aclose()

    async def set_connector(self, connector):
        await self._session.aclose()
        self._connector = connector
        await self.create_session()

    def sync_request(self, **_):
        raise NotImplementedError("sync_request is not implemented for asyncio handler")

    def threaded_request(self, **_):
        raise NotImplementedError("threaded_request is not implemented for asyncio handler")

    async def async_request(self, options_func, cancellation_event):
        """
        Query string should be provided as a manually serialized and encoded string.

        :param options_func:
        :param cancellation_event:
        :return:
        """
        if self._connector and self._connector.is_closed:
            raise RuntimeError('Session is closed')
        if cancellation_event is not None:
            assert isinstance(cancellation_event, Event)

        options = options_func()
        assert isinstance(options, RequestOptions)

        create_response = options.create_response
        create_status = options.create_status
        create_exception = options.create_exception

        params_to_merge_in = {}

        if options.operation_type == PNOperationType.PNPublishOperation:
            params_to_merge_in['seqn'] = await self.pubnub._publish_sequence_manager.get_next_sequence()

        options.merge_params_in(params_to_merge_in)

        if options.use_base_path:
            url = utils.build_url(self.pubnub.config.scheme(), self.pubnub.base_origin, options.path,
                                  options.query_string)
        else:
            url = utils.build_url(scheme="", origin="", path=options.path, params=options.query_string)

        full_url = httpx.URL(url, query=options.query_string.encode('utf-8'))

        logger.debug("%s %s %s" % (options.method_string, url, options.data))

        if options.request_headers:
            request_headers = {**self.pubnub.headers, **options.request_headers}
        else:
            request_headers = self.pubnub.headers

        request_arguments = {
            'method': options.method_string,
            'headers': request_headers,
            'url': full_url,
            'follow_redirects': options.allow_redirects,
            'timeout': (options.connect_timeout, options.request_timeout),
        }
        if options.is_post() or options.is_patch():
            request_arguments['content'] = options.data
            request_arguments['files'] = options.files

        try:
            if not self._session:
                await self.create_session()
            start_timestamp = time.time()
            response = await asyncio.wait_for(
                self._session.request(**request_arguments),
                options.request_timeout
            )
        except (asyncio.TimeoutError, asyncio.CancelledError):
            raise
        except Exception as e:
            logger.error("session.request exception: %s" % str(e))
            raise

        response_body = response.read()
        if not options.non_json_response:
            body = response_body
        else:
            if isinstance(response.content, bytes):
                body = response.content  # TODO: simplify this logic within the v5 release
            else:
                body = response_body

        if cancellation_event is not None and cancellation_event.is_set():
            return

        response_info = None
        status_category = PNStatusCategory.PNUnknownCategory

        if response:
            request_url = urllib.parse.urlparse(str(response.url))
            query = urllib.parse.parse_qs(request_url.query)
            uuid = None
            auth_key = None

            if 'uuid' in query and len(query['uuid']) > 0:
                uuid = query['uuid'][0]

            if 'auth_key' in query and len(query['auth_key']) > 0:
                auth_key = query['auth_key'][0]

            response_info = ResponseInfo(
                status_code=response.status_code,
                tls_enabled='https' == request_url.scheme,
                origin=request_url.hostname,
                uuid=uuid,
                auth_key=auth_key,
                client_request=None,
                client_response=response
            )

        # if body is not None and len(body) > 0 and not options.non_json_response:
        if body is not None and len(body) > 0:
            if options.non_json_response:
                data = body
            else:
                try:
                    data = json.loads(body)
                except ValueError:
                    if response.status == 599 and len(body) > 0:
                        data = body
                    else:
                        raise
                except TypeError:
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except ValueError:
                        raise create_exception(
                            category=status_category,
                            response=response,
                            response_info=response_info,
                            exception=PubNubException(
                                pn_error=PNERR_JSON_DECODING_FAILED,
                                errormsg='json decode error',
                            )
                        )
        else:
            data = "N/A"

        logger.debug(data)

        if response.status_code not in (200, 307, 204):

            if response.status_code >= 500:
                err = PNERR_SERVER_ERROR
            else:
                err = PNERR_CLIENT_ERROR

            if response.status_code == 403:
                status_category = PNStatusCategory.PNAccessDeniedCategory

            if response.status_code == 400:
                status_category = PNStatusCategory.PNBadRequestCategory

            raise create_exception(
                category=status_category,
                response=data,
                response_info=response_info,
                exception=PubNubException(
                    errormsg=data,
                    pn_error=err,
                    status_code=response.status_code
                )
            )
        else:
            self.pubnub._telemetry_manager.store_latency(time.time() - start_timestamp, options.operation_type)

            return AsyncioEnvelope(
                result=create_response(data) if not options.non_json_response else create_response(response, data),
                status=create_status(
                    PNStatusCategory.PNAcknowledgmentCategory,
                    data,
                    response_info,
                    None
                )
            )
