
class Suite():
    def __init__(self, pubnub, expected):
        self.pubnub = pubnub
        self.total = expected
        self.passed = 0
        self.failed = 0
        self.started = False

    def test(self, condition, name, message=None, response=None):

        if condition:
            self.passed += 1
            msg = "PASS : " + name
            if message:
                msg += ", " + message
            if response:
                msg += ", " + response
            print(msg)
        else:
            self.failed += 1
            msg = "FAIL : " + name
            if message:
                msg += ", " + message
            if response:
                msg += ", " + response
            print(msg)

        if self.total == self.failed + self.passed:
            print("\n======== RESULT ========")
            print("Total\t:\t", self.total)
            print("Passed\t:\t", self.passed)
            print("Failed\t:\t", self.failed)
            self.pubnub.stop()
