from abc import abstractmethod


class PubNubCrypto:
    def __init__(self, pubnub_config):
        self.pubnub_configuration = pubnub_config

    @abstractmethod
    def encrypt(self, key, msg):
        pass

    @abstractmethod
    def decrypt(self, key, msg):
        pass
