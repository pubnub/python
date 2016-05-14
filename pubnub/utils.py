import json
import urllib


def get_data_for_user(data):
    try:
        if 'message' in data and 'payload' in data:
            return {'message': data['message'], 'payload': data['payload']}
        else:
            return data
    except TypeError:
        return data


def encode(data):
    if isinstance(data, str):
        return quote("\"%s\"" % data)
    else:
        return quote(json.dumps(data))


def quote(data):
    try:
        from urllib.parse import quote as q
    except ImportError:
        import urllib.quote as q

    q(data)
