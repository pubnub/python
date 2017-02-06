from abc import abstractmethod


class PubNubCrypto:
    @abstractmethod
    def encrypt(self, key, msg):
        pass

    @abstractmethod
    def decrypt(self, key, msg):
        pass
