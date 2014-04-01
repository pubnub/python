try:
    import urllib.request
except:
    import urllib2

import threading
import json
import time

current_req_id = -1

class HTTPClient:
    def __init__(self, url, callback, id=None):
        self.url = url
        self.id = id
        self.callback = callback
        self.stop = False

    def cancel(self):
        self.stop = True
        self.callback = None

    def run(self):
        global current_req_id
        data = urllib2.urlopen(self.url, timeout=310).read()
        if self.stop is True:
            return
        if self.id is not None and current_req_id != self.id:
            return
        if self.callback is not None:
            self.callback(json.loads(data))


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

    def timeout(self, interval, func):
        def cb():
            time.sleep(interval)
            func()
        thread = threading.Thread(target=cb)
        thread.start()

    def _request2_async( self, request, callback, single=False ) :
        global current_req_id
        ## Build URL
        url = self.getUrl(request)
        if single is True:
            id = time.time()
            client = HTTPClient(url, callback, id)
            current_req_id = id
        else:
            client = HTTPClient(url, callback)

        thread = threading.Thread(target=client.run)
        thread.start()
        def abort():
            client.cancel();
        return abort


    def _request2_sync( self, request) :

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
            
            return resp_json


    def _request2(self, request, callback=None, single=False):
        if callback is None:
            return self._request2_sync(request,single=single)
        else:
            self._request2_async(request, callback, single=single)



    def _request3_sync( self, request) :
        ## Build URL
        url = self.getUrl(request)
        ## Send Request Expecting JSONP Response
        try:
            response = urllib.request.urlopen(url,timeout=310)
            resp_json = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            return None
            
        return resp_json

    def _request3_async( self, request, callback, single=False ) :
        pass

    def _request3(self, request, callback=None, single=False):
        if callback is None:
            return self._request3_sync(request,single=single)
        else:
            self._request3_async(request, callback, single=single)
