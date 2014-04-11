try:
    import urllib.request
except:
    import urllib2

import threading
import json
import time
import threading
from threading import current_thread

latest_sub_callback_lock = threading.RLock()
latest_sub_callback = {'id' : None, 'callback' : None}

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
        data = urllib2.urlopen(self.url, timeout=310).read()
        if self.stop is True:
            return
        if self.callback is None:
            global latest_sub_callback
            global latest_sub_callback_lock
            with latest_sub_callback_lock:
                if latest_sub_callback['id'] != self.id:
                    return
                else:
                    print(data)
                    if latest_sub_callback['callback'] is not None:
                        latest_sub_callback['id'] = 0
                        latest_sub_callback['callback'](json.loads(data))
        else:
            self.callback(json.loads(data))


class Pubnub(PubnubCoreAsync):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key = False,
        cipher_key = False,
        auth_key = None,
        ssl_on = False,
        origin = 'pubsub.pubnub.com',
        pres_uuid = None
    ) :
        super(Pubnub, self).__init__(
            publish_key = publish_key,
            subscribe_key = subscribe_key,
            secret_key = secret_key,
            cipher_key = cipher_key,
            auth_key = auth_key,
            ssl_on = ssl_on,
            origin = origin,
            uuid = pres_uuid
        )
        if self.python_version == 2:
            self._request = self._request2
        else:
            self._request = self._request3
        self._channel_list_lock = threading.RLock()

    def timeout(self, interval, func):
        def cb():
            time.sleep(interval)
            func()
        thread = threading.Thread(target=cb)
        thread.start()

    def _request2_async( self, request, callback, single=False ) :
        ## Build URL
        url = self.getUrl(request)
        if single is True:
            id = time.time()
            client = HTTPClient(url, None, id)
            with latest_sub_callback_lock:
                latest_sub_callback['id'] = id
                latest_sub_callback['callback'] = callback
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
        except Exception as e:
            print e
            return None
            
        return resp_json


    def _request2(self, request, callback=None, single=False):
        if callback is None:
            return self._request2_sync(request)
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
