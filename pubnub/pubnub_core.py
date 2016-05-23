import logging
from abc import ABCMeta, abstractmethod

import requests
from requests import ConnectionError
from requests.packages.urllib3.exceptions import HTTPError

from .managers.publish_sequence_manager import PublishSequenceManager
from .endpoints.pubsub.publish import Publish
from .endpoints.presence.herenow import HereNow
from .structures import RequestOptions
from .exceptions import PubNubException
from .errors import PNERR_CLIENT_TIMEOUT, PNERR_HTTP_ERROR, PNERR_CONNECTION_ERROR, PNERR_TOO_MANY_REDIRECTS_ERROR, \
    PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_UNKNOWN_ERROR


logger = logging.getLogger("pubnub")


class PubNubCore:
    """A base class for PubNub Python API implementations"""
    SDK_VERSION = "4.0.0"
    SDK_NAME = "PubNub-Python"

    TIMESTAMP_DIVIDER = 1000
    MAX_SEQUENCE = 65535

    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config
        self.session = requests.Session()

        self.config.validate()
        self.headers = {
            'User-Agent': self.sdk_name
        }

        self.publish_sequence_manager = PublishSequenceManager(PubNubCore.MAX_SEQUENCE)

    def request_sync(self, options):
        return pn_request(self.session, self.config.scheme_and_host(), self.headers, options,
                          self.config.connect_timeout, self.config.non_subscribe_request_timeout)

    @abstractmethod
    def request_async(self, options, success, error):
        pass

    @abstractmethod
    def request_deferred(self, options_func):
        pass

    @abstractmethod
    def async_error_to_return(self, e, errback):
        pass

    def here_now(self):
        return HereNow(self)

    def publish(self):
        return Publish(self, self.publish_sequence_manager)

    @property
    def sdk_name(self):
        return "%s%s/%s" % (PubNubCore.SDK_NAME, self.sdk_platform(), PubNubCore.SDK_VERSION)

    @abstractmethod
    def sdk_platform(self): pass

    @property
    def uuid(self):
        return self.config.uuid


def pn_request(session, scheme_and_host, headers, options, connect_timeout, read_timeout):
    assert isinstance(options, RequestOptions)
    url = scheme_and_host + options.path

    args = {
        "method": options.method_string,
        'headers': headers,
        "url": url,
        'params': options.query_string,
        'timeout': (connect_timeout, read_timeout)
    }

    if options.is_post():
        args['data'] = options.data
        logger.debug("%s %s %s %s" % (options.method_string, url, options.params, options.data))
    else:
        logger.debug("%s %s %s" % (options.method_string, url, options.params))

    # connection error
    try:
        res = session.request(**args)
    except ConnectionError as e:
        raise PubNubException(
            pn_error=PNERR_CONNECTION_ERROR,
            errormsg=str(e)
        )
    except HTTPError as e:
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

    return res.json()
