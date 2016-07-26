import unittest

from pubnub import crypto

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
