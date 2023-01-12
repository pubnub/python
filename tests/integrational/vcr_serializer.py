import os
import re
from vcr.serializers.jsonserializer import serialize, deserialize


class PNJsonSerializer:
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
            interaction['request']['uri'] = self.replace_keys(interaction['request']['uri'])
            cassette_dict['interactions'][index] == interaction
        return serialize(cassette_dict)

    def replace_placeholders(self, interaction_dict):
        for key in self.envs.keys():
            interaction_dict['request']['uri'] = re.sub(f'{{{key}}}',
                                                        self.envs[key],
                                                        interaction_dict['request']['uri'])
        return interaction_dict

    def deserialize(self, cassette_string):
        cassette_dict = deserialize(cassette_string)
        cassette_dict['interactions'] = [self.replace_placeholders(interaction)
                                         for interaction in cassette_dict['interactions']]
        return cassette_dict
