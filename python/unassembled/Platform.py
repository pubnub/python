def _pubnub_request_instance(request, url, callback=None):
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


class Pubnub(PubnubCore):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key = False,
        cipher_key = False,
        ssl_on = False,
        origin = 'pubsub.pubnub.com',
        pres_uuid = None,
        workers = 10
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
        self._number_of_workers = workers
        self.pool = None

    def has_pool(self):
        if self.pool == 'error':
            return False
        if self.pool is not None:
            # Already instanciated
            return True
        # Making new pool
        try:
            from multiprocessing import Pool
        except ImportError:
            self.pool = 'error'
            return False
        self.pool = Pool(processes=self._number_of_workers)
        return True

    def _request( self, request, callback = None, blocking = True ) :
        # If `blocking` is False it will return immediately without data.
        # If `blocking` is True it will return the JSON data from the server

        ## Build URL
        url = self.getUrl(request)

        ## Send Request Expecting JSONP Response
        args = [request, url, callback]

        if blocking is False and self.has_pool():
            self.pool.apply_async(_pubnub_request_instance, args)
        else:
            return _pubnub_request_instance(*args)
