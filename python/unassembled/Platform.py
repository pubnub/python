try:
    import urllib.request
except:
    import urllib2

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
        if self.python_version == 2:
            self._request = self._request2
        else:
            self._request = self._request3

    def _request2( self, request, callback = None ) :
        ## Build URL
        url = self.getUrl(request)

        ## Send Request Expecting JSONP Response
        try:
            try: usock = urllib2.urlopen( url, None, 310 )
            except TypeError: usock = urllib2.urlopen( url, None )
            response = usock.read()
            usock.close()
            resp_json = json.loads(response)
        except:
            return None
            
        if (callback):
            callback(resp_json)
        else:
            return resp_json


    def _request3( self, request, callback = None ) :
        ## Build URL
        url = self.getUrl(request)
        ## Send Request Expecting JSONP Response
        try:
            response = urllib.request.urlopen(url,timeout=310)
            resp_json = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(e)
            return None
            
        if (callback):
            callback(resp_json)
        else:
            return resp_json
