import json
import urllib
import uuid as u

try:
    from urllib.parse import urlunsplit as pn_urlunsplit
except ImportError:
    from urlparse import urlunsplit as pn_urlunsplit

try:
    from urllib.parse import urlencode as pn_urlencode
except ImportError:
    from urlparse import urlencode as pn_urlencode


def get_data_for_user(data):
    try:
        if 'message' in data and 'payload' in data:
            return {'message': data['message'], 'payload': data['payload']}
        else:
            return data
    except TypeError:
        return data


def write_value_as_string(data):
    if isinstance(data, str):
        return ("\"%s\"" % data).replace("+", "%20")
    else:
        return json.dumps(data).replace("+", "%20")


def url_encode(data):
    try:
        from urllib.parse import quote as q
    except ImportError:
        from urllib import quote as q

    return q(data)


def uuid():
    return str(u.uuid4())


def build_url(scheme, origin, path, params):
    return pn_urlunsplit((scheme, origin, path, pn_urlencode(params), ''))
