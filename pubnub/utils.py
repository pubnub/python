import datetime
import hmac
import json
import uuid as u
import threading

try:
    from hashlib import sha256

    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod

    sha256 = digestmod.new

import six

from .enums import PNStatusCategory, PNOperationType, PNPushType
from .models.consumer.common import PNStatus
from .errors import PNERR_JSON_NOT_SERIALIZABLE
from .exceptions import PubNubException


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
            return "\"%s\"" % data
        else:
            return json.dumps(data)
    except TypeError:
        raise PubNubException(
            pn_error=PNERR_JSON_NOT_SERIALIZABLE
        )


def url_encode(data):
    return six.moves.urllib.parse.quote(data, safe="").replace("+", "%2B")


def url_write(data):
    """ Just wraps url_encode(write_value_as_string()) """
    return url_encode(write_value_as_string(data))


def uuid():
    return str(u.uuid4())


def split_items(items_string):
    if len(items_string) is 0:
        return []
    else:
        return items_string.split(",")


def join_items(items_list):
    return ",".join(items_list)


def join_items_and_encode(items_list):
    return ",".join(url_encode(x) for x in items_list)


def join_channels(items_list):
    if len(items_list) == 0:
        return ","
    else:
        return join_items_and_encode(items_list)


def extend_list(existing_items, new_items):
    if isinstance(new_items, six.string_types):
        existing_items.extend(split_items(new_items))
    else:
        existing_items.extend(new_items)


def build_url(scheme, origin, path, params={}):
    return six.moves.urllib.parse.urlunsplit((scheme, origin, path, params, ''))


def synchronized(func):
    func.__lock__ = threading.Lock()

    def synced_func(*args, **kws):
        with func.__lock__:
            return func(*args, **kws)

    return synced_func


def is_subscribed_event(status):
    assert isinstance(status, PNStatus)
    return status.category == PNStatusCategory.PNConnectedCategory


def is_unsubscribed_event(status):
    assert isinstance(status, PNStatus)
    return status.category == PNStatusCategory.PNAcknowledgmentCategory \
        and status.operation == PNOperationType.PNUnsubscribeOperation


def prepare_pam_arguments(unsorted_params):
    sorted_keys = sorted(unsorted_params)
    stringified_arguments = ""
    i = 0

    for key in sorted_keys:
        if i != 0:
            stringified_arguments += "&"

        stringified_arguments += (key + "=" + pam_encode(str(unsorted_params[key])))
        i += 1

    return stringified_arguments


def pam_encode(s_url):
    # !'()*~
    encoded = url_encode(s_url)
    if encoded is not None:
        encoded = (encoded.replace("*", "%2A")
                   .replace("!", "%21")
                   .replace("'", "%27")
                   .replace("(", "%28")
                   .replace(")", "%29")
                   .replace("[", "%5B")
                   .replace("]", "%5D")
                   .replace("~", "%7E"))

    return encoded


def sign_sha256(secret, sign_input):
    from base64 import urlsafe_b64encode

    sign = urlsafe_b64encode(hmac.new(
        secret.encode("utf-8"),
        sign_input.encode("utf-8"),
        sha256
    ).digest())

    return sign.decode("utf-8")


def push_type_to_string(push_type):
    if push_type == PNPushType.APNS:
        return "apns"
    elif push_type == PNPushType.GCM:
        return "gcm"
    elif push_type == PNPushType.MPNS:
        return "mpns"
    else:
        return ""


def strip_right(text, suffix):
    if not text.endswith(suffix):
        return text

    return text[:len(text) - len(suffix)]


def datetime_now():
    return datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
