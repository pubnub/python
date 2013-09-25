
class Pubnub(PubnubCore):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key = False,
        cipher_key = False,
        ssl_on = False,
        origin = 'pubsub.pubnub.com',
        pres_uuid = None
    ) :
        super(Pubnub, self).__init__(
            publish_key = publish_key,
            subscribe_key = subscribe_key,
            secret_key = secret_key,
            cipher_key = cipher_key,
            ssl_on = ssl_on,
            origin = origin,
            uuid = pres_uuid
        )        

    def _request( self, request, callback = None ) :
        ## Build URL
        url = self.getUrl(request)

        ## Send Request Expecting JSONP Response
        try:
            try: usock = urllib2.urlopen( url, None, 200 )
            except TypeError: usock = urllib2.urlopen( url, None )
            response = usock.read()
            usock.close()
            if (callback):
                callback(json.loads(response))
            else:
                return json.loads( response )
        except:
            return None
