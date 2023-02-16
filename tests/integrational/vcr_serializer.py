import os
import re
from base64 import b64decode, b64encode
from vcr.serializers.jsonserializer import serialize, deserialize


class PNSerializer:
    patterns = ['pub-c-[a-z0-9-]{36}', 'sub-c-[a-z0-9-]{36}']
    envs = {}

    def __init__(self) -> None:
        self.envs = {key: value for key, value in os.environ.items() if key.startswith('PN_KEY_')}

    def replace_keys(self, cassette_string):
        for pattern in self.patterns:
            found = re.search(pattern, cassette_string)
            if found and found.group(0) in list(self.envs.values()):
                key = list(self.envs.keys())[list(self.envs.values()).index(found.group(0))]
                if key:
                    cassette_string = re.sub(pattern, f'{{{key}}}', cassette_string)
        return cassette_string

    def serialize(self, cassette_dict):
        for index, interaction in enumerate(cassette_dict['interactions']):
            # for serializing binary body
            if type(interaction['response']['body']['string']) is bytes:
                ascii_body = b64encode(interaction['response']['body']['string']).decode('ascii')
                interaction['response']['body'] = {'binary': ascii_body}

            cassette_dict['interactions'][index] == interaction
        return self.replace_keys(serialize(cassette_dict))

    def replace_placeholders(self, cassette_string):
        for key in self.envs.keys():
            cassette_string = re.sub(f'{{{key}}}', self.envs[key], cassette_string['request']['uri'])

    def deserialize(self, cassette_string):
        cassette_string = self.replace_placeholders(cassette_string)
        cassette_dict = deserialize(cassette_string)
        for index, interaction in enumerate(cassette_dict['interactions']):
            interaction = self.replace_placeholders(interaction)
            if 'binary' in interaction['response']['body'].keys():
                interaction['response']['body']['string'] = b64decode(interaction['response']['body']['binary'])
                del interaction['response']['body']['binary']
            cassette_dict['interactions'][index] == interaction
        return cassette_dict
