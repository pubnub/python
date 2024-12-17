import os
import re
from base64 import b64decode, b64encode
from vcr.serializers.jsonserializer import serialize, deserialize
from pickle import dumps, loads


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
            if interaction['request']['body']:
                picklebody = b64encode(dumps(interaction['request']['body'])).decode('ascii')
                interaction['request']['body'] = {'pickle': picklebody}
            if interaction['response']['body']:
                picklebody = b64encode(dumps(interaction['response']['body'])).decode('ascii')
                interaction['response']['body'] = {'pickle': picklebody}

        return self.replace_keys(serialize(cassette_dict))

    def replace_placeholders(self, cassette_string):
        for key in self.envs.keys():
            cassette_string = re.sub(f'{{{key}}}', self.envs[key], cassette_string)
        return cassette_string

    def deserialize(self, cassette_string):
        cassette_dict = deserialize(self.replace_placeholders(cassette_string))
        for index, interaction in enumerate(cassette_dict['interactions']):
            if isinstance(interaction['request']['body'], dict) and 'pickle' in interaction['request']['body'].keys():
                interaction['request']['body'] = loads(b64decode(interaction['request']['body']['pickle']))
            if isinstance(interaction['response']['body'], dict) and 'pickle' in interaction['response']['body'].keys():
                interaction['response']['body'] = loads(b64decode(interaction['response']['body']['pickle']))
            cassette_dict['interactions'][index] == interaction
        return cassette_dict
