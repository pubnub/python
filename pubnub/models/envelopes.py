class AsyncioEnvelope:
    def __init__(self, result, status):
        self.result = result
        self.status = status

    @staticmethod
    def is_error():
        return False
