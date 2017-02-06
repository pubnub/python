import unittest

from pubnub.crypto import PubNubCryptodome
from tests.helper import gen_decrypt_func

crypto = PubNubCryptodome()
todecode = 'QfD1NCBJCmt1aPPGU2cshw=='
key = 'testKey'


class TestDecode(unittest.TestCase):
    def test_decode_aes(self):
        hey = """

        dfjn
        t564

        sdfhp\n
        """

        assert crypto.decrypt(key, crypto.encrypt(key, hey)) == hey
        assert crypto.decrypt(key, todecode) == "hey-0"

    def test_vc_body_decoder(self):
        input = b'"9P/7+NNs54o7Go41yh+3rIn8BW0H0ad+mKlKTKGw2i1eoQP1ddHrnIzkRUPEC3ko"'
        # print(json.loads(input.decode('utf-8')))
        assert {"name": "Alex", "online": True} == \
            gen_decrypt_func('testKey')(input.decode('utf-8'))
