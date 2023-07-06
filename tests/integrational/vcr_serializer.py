import os
import re
from base64 import b64decode, b64encode
from vcr.serializers.jsonserializer import serialize, deserialize


class PNSerializer:
    patterns = ['pub-c-[a-z0-9-]{36}', 'sub-c-[a-z0-9-]{36}']
    envs = {}

    def __init__(self) -> None:
        self.envs = {key: value for key, value in os.environ.items() if key.startswith('PN_KEY_')}

    def replace_keys(self, uri_string):
        for pattern in self.patterns:
            found = re.search(pattern, uri_string)
            if found and found.group(0) in list(self.envs.values()):
                key = list(self.envs.keys())[list(self.envs.values()).index(found.group(0))]
                if key:
                    uri_string = re.sub(pattern, f'{{{key}}}', uri_string)
        return uri_string

    def serialize(self, cassette_dict):
        for index, interaction in enumerate(cassette_dict['interactions']):
            # for serializing binary body
            if type(interaction['request']['body']) is bytes:
                ascii_body = b64encode(interaction['request']['body']).decode('ascii')
                interaction['request']['body'] = {'binary': ascii_body}
            if type(interaction['response']['body']['string']) is bytes:
                ascii_body = b64encode(interaction['response']['body']['string']).decode('ascii')
                interaction['response']['body'] = {'binary': ascii_body}

        return self.replace_keys(serialize(cassette_dict))

    def replace_placeholders(self, cassette_string):
        for key in self.envs.keys():
            cassette_string = re.sub(f'{{{key}}}', self.envs[key], cassette_string)
        return cassette_string

    def deserialize(self, cassette_string):
        cassette_dict = deserialize(self.replace_placeholders(cassette_string))
        for index, interaction in enumerate(cassette_dict['interactions']):
            if 'binary' in interaction['response']['body'].keys():
                interaction['response']['body']['string'] = b64decode(interaction['response']['body']['binary'])
                del interaction['response']['body']['binary']
            cassette_dict['interactions'][index] == interaction
        return cassette_dict
