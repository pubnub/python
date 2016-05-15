import json


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
        return "\"%s\"" % data
    else:
        return json.dumps(data)


def url_encode(data):
    try:
        from urllib.parse import quote as q
    except ImportError:
        from urllib import quote as q

    return q(data)
