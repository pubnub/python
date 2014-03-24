import urllib3

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
        self.http = urllib3.PoolManager(timeout=310)     

    def _request( self, request, callback = None ) :
        ## Build URL
        url = self.getUrl(request)

        ## Send Request Expecting JSONP Response
        try:
            response = self.http.request('GET', url)
            resp_json = json.loads(response.data.decode("utf-8"))
        except:
            return None
            
        if (callback):
            callback(resp_json)
        else:
            return resp_json
