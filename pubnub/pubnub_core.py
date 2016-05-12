from abc import ABCMeta, abstractmethod

from pip._vendor import requests
from pip._vendor.requests import ConnectionError
from pip._vendor.requests.packages.urllib3.exceptions import HTTPError

from .endpoints.presence.herenow import HereNow
from .exceptions import PubNubException
from .errors import PNERR_CLIENT_TIMEOUT, PNERR_HTTP_ERROR, PNERR_CONNECTION_ERROR, PNERR_TOO_MANY_REDIRECTS_ERROR, \
    PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_UNKNOWN_ERROR


class PubNubCore:
    """A base class for PubNub Python API implementations"""

    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config
        self.session = requests.Session()

    def request_sync(self, path, query):
        url = self.config.scheme_and_host() + path
        print(url)

        # connection error
        try:
            res = self.session.get(url, params=query)
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
            raise PubNubException (
                pn_error=PNERR_UNKNOWN_ERROR,
                errormsg=str(e)
            )

        # server error
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

    def here_now(self):
        return HereNow(self)

    @property
    def version(self):
        return "4.0.0"

    @property
    def uuid(self):
        return self.config.uuid
