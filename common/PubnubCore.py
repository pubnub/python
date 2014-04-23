class PubnubCore(PubnubCoreAsync):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        uuid=None
    ):
        """
        #**
        #* Pubnub
        #*
        #* Init the Pubnub Client API
        #*
        #* @param string publish_key required key to send messages.
        #* @param string subscribe_key required key to receive messages.
        #* @param string secret_key optional key to sign messages.
        #* @param boolean ssl required for 2048 bit encrypted messages.
        #* @param string origin PUBNUB Server Origin.
        #* @param string pres_uuid optional
        #*  identifier for presence (auto-generated if not supplied)
        #**

        ## Initiat Class
        pubnub = Pubnub( 'PUBLISH-KEY', 'SUBSCRIBE-KEY', 'SECRET-KEY', False )

        """
        super(PubnubCore, self).__init__(
            publish_key=publish_key,
            subscribe_key=subscribe_key,
            secret_key=secret_key,
            cipher_key=cipher_key,
            auth_key=auth_key,
            ssl_on=ssl_on,
            origin=origin,
            UUID=uuid
        )

        self.subscriptions = {}
        self.timetoken = 0
        self.version = '3.4'
        self.accept_encoding = 'gzip'

    def subscribe_sync(self, channel, callback, timetoken=0):
        """
        #**
        #* Subscribe
        #*
        #* This is BLOCKING.
        #* Listen for a message on a channel.
        #*
        #* @param array args with channel and callback.
        #* @return false on fail, array on success.
        #**

        ## Subscribe Example
        def receive(message) :
            print(message)
            return True

        pubnub.subscribe({
            'channel'  : 'hello_world',
            'callback' : receive
        })

        """

        subscribe_key = self.subscribe_key

        ## Begin Subscribe
        while True:

            try:
                ## Wait for Message
                response = self._request({"urlcomponents": [
                    'subscribe',
                    subscribe_key,
                    channel,
                    '0',
                    str(timetoken)
                ], "urlparams": {"uuid": self.uuid}})

                messages = response[0]
                timetoken = response[1]

                ## If it was a timeout
                if not len(messages):
                    continue

                ## Run user Callback and Reconnect if user permits.
                for message in messages:
                    if not callback(self.decrypt(message)):
                        return

            except Exception:
                time.sleep(1)

        return True
