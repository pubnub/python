class PNHistoryResult(object):
    def __init__(self, messages, start_timetoken, end_timetoken):
        self.messages = messages
        self.start_timetoken = start_timetoken
        self.end_timetoken = end_timetoken

    def __str__(self):
        return "History result for range %d..%d" % (self.start_timetoken, self.end_timetoken)

    @classmethod
    def from_json(cls, json_input, crypto, include_timetoken=False, include_meta=False, cipher=None):
        start_timetoken = json_input[1]
        end_timetoken = json_input[2]

        raw_items = json_input[0]
        messages = []

        for item in raw_items:
            if (include_timetoken or include_meta) and isinstance(item, dict) and 'message' in item:
                message = PNHistoryItemResult(item['message'], crypto)
                if include_timetoken and 'timetoken' in item:
                    message.timetoken = item['timetoken']
                if include_meta and 'meta' in item:
                    message.meta = item['meta']

            else:
                message = PNHistoryItemResult(item, crypto)

            if cipher is not None:
                message.decrypt(cipher)

            messages.append(message)

        return PNHistoryResult(
            messages=messages,
            start_timetoken=start_timetoken,
            end_timetoken=end_timetoken
        )


class PNHistoryItemResult(object):
    def __init__(self, entry, crypto, timetoken=None, meta=None):
        self.timetoken = timetoken
        self.meta = meta
        self.entry = entry
        self.crypto = crypto

    def __str__(self):
        return "History item with tt: %s and content: %s" % (self.timetoken, self.entry)

    def decrypt(self, cipher_key):
        self.entry = self.crypto.decrypt(cipher_key, self.entry)


class PNFetchMessagesResult(object):

    def __init__(self, channels, start_timetoken, end_timetoken):
        self.channels = channels
        self.start_timetoken = start_timetoken
        self.end_timetoken = end_timetoken

    def __str__(self):
        return "Fetch messages result for range %d..%d" % (self.start_timetoken, self.end_timetoken)

    @classmethod
    def from_json(cls, json_input, include_message_actions=False, start_timetoken=None, end_timetoken=None):
        channels = {}

        for key, entry in json_input['channels'].items():
            channels[key] = []
            for item in entry:
                message = PNFetchMessageItem(item['message'], item['timetoken'])
                if 'meta' in item:
                    message.meta = item['meta']

                if include_message_actions:
                    if 'actions' in item:
                        message.actions = item['actions']
                    else:
                        message.actions = {}

                channels[key].append(message)

        return PNFetchMessagesResult(
            channels=channels,
            start_timetoken=start_timetoken,
            end_timetoken=end_timetoken
        )


class PNFetchMessageItem(object):
    def __init__(self, message, timetoken, meta=None, actions=None):
        self.message = message
        self.meta = meta
        self.timetoken = timetoken
        self.actions = actions

    def __str__(self):
        return "Fetch message item with tt: %s and content: %s" % (self.timetoken, self.message)
