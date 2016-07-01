import json
import uuid as u
import threading

import six

from .errors import PNERR_JSON_NOT_SERIALIZABLE
from .exceptions import PubNubException

# TODO: migrate to :six: helpers instead of following
try:
    from urllib.parse import urlunsplit as pn_urlunsplit
except ImportError:
    from urlparse import urlunsplit as pn_urlunsplit

try:
    from urllib.parse import urlparse as pn_urlparse
except ImportError:
    from urlparse import urlparse as pn_urlparse

try:
    from urllib.parse import urlencode as pn_urlencode
except ImportError:
    from urllib import urlencode as pn_urlencode

try:
    from urllib.parse import parse_qs as pn_parse_qs
except ImportError:
    from urlparse import parse_qs as pn_parse_qs

try:
    from queue import Queue as Queue
except ImportError:
    from Queue import Queue as Queue

try:
    from queue import Empty as QueueEmpty
except ImportError:
    from Queue import Empty as QueueEmpty


def get_data_for_user(data):
    try:
        if 'message' in data and 'payload' in data:
            return {'message': data['message'], 'payload': data['payload']}
        else:
            return data
    except TypeError:
        return data


def write_value_as_string(data):
    try:
        if isinstance(data, six.string_types):
            return ("\"%s\"" % data).replace("+", "%20")
        else:
            return json.dumps(data).replace("+", "%20")
    except TypeError:
        raise PubNubException(
            pn_error=PNERR_JSON_NOT_SERIALIZABLE
        )


def url_encode(data):
    try:
        from urllib.parse import quote as q
    except ImportError:
        from urllib import quote as q

    return q(data)


def uuid():
    return str(u.uuid4())


def split_items(items_string):
    if len(items_string) is 0:
        return []
    else:
        return items_string.split(",")


def join_items(items_list):
    return ",".join(items_list)


def join_channels(items_list):
    if len(items_list) == 0:
        return ","
    else:
        return join_items(items_list)


def extend_list(existing_items, new_items):
    if isinstance(new_items, six.string_types):
        existing_items.extend(split_items(new_items))
    else:
        existing_items.extend(new_items)


def build_url(scheme, origin, path, params={}):
    return pn_urlunsplit((scheme, origin, path, params, ''))


def synchronized(func):
    func.__lock__ = threading.Lock()

    def synced_func(*args, **kws):
        with func.__lock__:
            return func(*args, **kws)

    return synced_func

urlparse = pn_urlparse
parse_qs = pn_parse_qs
