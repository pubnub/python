import datetime
import hmac
import json
import uuid as u
import threading
import urllib
from hashlib import sha256

from .enums import PNStatusCategory, PNOperationType, PNPushType, HttpMethod
from .models.consumer.common import PNStatus
from .errors import PNERR_JSON_NOT_SERIALIZABLE, PNERR_PERMISSION_MISSING
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
        if isinstance(data, str):
            return "\"%s\"" % data
        else:
            return json.dumps(data)
    except TypeError:
        raise PubNubException(
            pn_error=PNERR_JSON_NOT_SERIALIZABLE
        )


def url_encode(data):
    return urllib.parse.quote(data, safe="~").replace("+", "%2B")


def url_write(data):
    """ Just wraps url_encode(write_value_as_string()) """
    return url_encode(write_value_as_string(data))


def uuid():
    return str(u.uuid4())


def split_items(items_string):
    if len(items_string) == 0:
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
    if isinstance(new_items, str):
        existing_items.extend(split_items(new_items))
    else:
        existing_items.extend(new_items)


def build_url(scheme, origin, path, params={}):
    return urllib.parse.urlunsplit((scheme, origin, path, params, ''))


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


def sign_request(endpoint, pn, custom_params, method, body):
    custom_params['timestamp'] = str(pn.timestamp())

    request_url = endpoint.build_path()

    encoded_query_string = prepare_pam_arguments(custom_params)

    is_v2_signature = not (request_url.startswith("/publish") and method == HttpMethod.POST)

    signed_input = ""
    if not is_v2_signature:
        signed_input += pn.config.subscribe_key + "\n"
        signed_input += pn.config.publish_key + "\n"
        signed_input += request_url + "\n"
        signed_input += encoded_query_string
    else:
        signed_input += HttpMethod.string(method).upper() + "\n"
        signed_input += pn.config.publish_key + "\n"
        signed_input += request_url + "\n"
        signed_input += encoded_query_string + "\n"
        if body is not None:
            signed_input += body

    signature = sign_sha256(pn.config.secret_key, signed_input)
    if is_v2_signature:
        signature = signature.rstrip("=")
        signature = "v2." + signature

    custom_params['signature'] = signature


def parse_resources(resource_list, resource_set_name, resources, patterns):
    if resource_list is not None:
        for pn_resource in resource_list:
            resource_object = {}

            if pn_resource.is_pattern_resource():
                determined_object = patterns
            else:
                determined_object = resources

            if resource_set_name in determined_object:
                determined_object[resource_set_name][pn_resource.get_id()] = calculate_bitmask(pn_resource)
            else:
                resource_object[pn_resource.get_id()] = calculate_bitmask(pn_resource)
                determined_object[resource_set_name] = resource_object

    if resource_set_name not in resources:
        resources[resource_set_name] = {}

    if resource_set_name not in patterns:
        patterns[resource_set_name] = {}


def calculate_bitmask(pn_resource):
    bit_sum = 0
    from .endpoints.access.grant_token import GrantToken

    if pn_resource.is_read() is True:
        bit_sum += GrantToken.READ

    if pn_resource.is_write() is True:
        bit_sum += GrantToken.WRITE

    if pn_resource.is_manage() is True:
        bit_sum += GrantToken.MANAGE

    if pn_resource.is_delete() is True:
        bit_sum += GrantToken.DELETE

    if pn_resource.is_create() is True:
        bit_sum += GrantToken.CREATE

    if bit_sum == 0:
        raise PubNubException(pn_error=PNERR_PERMISSION_MISSING)

    return bit_sum


def decode_utf8_dict(dic):
    if isinstance(dic, bytes):
        return dic.decode("utf-8")
    elif isinstance(dic, dict):
        new_dic = {}

        for key in dic:
            new_key = key
            if isinstance(key, bytes):
                new_key = key.decode("UTF-8")

            if new_key == "sig" and isinstance(dic[key], bytes):
                new_dic[new_key] = dic[key]
            else:
                new_dic[new_key] = decode_utf8_dict(dic[key])

        return new_dic
    elif isinstance(dic, list):
        new_l = []
        for e in dic:
            new_l.append(decode_utf8_dict(e))
        return new_l
    else:
        return dic
