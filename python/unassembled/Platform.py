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
    def __init__(self, url, urllib_func=None, callback=None, error=None, id=None):
        self.url = url
        self.id = id
        self.callback = callback
        self.error = error
        self.stop = False
        self._urllib_func = urllib_func

    def cancel(self):
        self.stop = True
        self.callback = None
        self.error = None


    def run(self):

        def _invoke(func, data):
            if func is not None:
                func(data)

        if self._urllib_func is None:
            return

        '''
        try:
            resp = urllib2.urlopen(self.url, timeout=320)
        except urllib2.HTTPError as http_error:
            resp = http_error
        '''
        resp = self._urllib_func(self.url, timeout=320)
        data = resp[0]
        code = resp[1]

        if self.stop is True:
            return
        if self.callback is None:
            global latest_sub_callback
            global latest_sub_callback_lock
            with latest_sub_callback_lock:
                if latest_sub_callback['id'] != self.id:
                    return
                else:
                    if latest_sub_callback['callback'] is not None:
                        latest_sub_callback['id'] = 0
                        try:
                            data = json.loads(data)
                        except:
                            _invoke(latest_sub_callback['error'], {'error' : 'json decoding error'})
                            return
                        if code != 200:
                            _invoke(latest_sub_callback['error'],data)
                        else:
                            _invoke(latest_sub_callback['callback'],data)
        else:
            try:
                data = json.loads(data)
            except:
                _invoke(self.error, {'error' : 'json decoding error'})
                return

            if code != 200:
                _invoke(self.error,data)
            else:
                _invoke(self.callback,data)


def _urllib_request_2(url, timeout=320):
    try:
        resp = urllib2.urlopen(url,timeout=timeout)
    except urllib2.HTTPError as http_error:
        resp = http_error
    return (resp.read(),resp.code)

def _urllib_request_3(url, timeout=320):
    #print(url)
    try:
        resp = urllib.request.urlopen(url,timeout=timeout)
    except urllib.request.HTTPError as http_error:
        resp = http_error
    r =   resp.read().decode("utf-8")
    #print(r)
    return (r,resp.code)

_urllib_request = None

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
            uuid = pres_uuid,
            _tt_lock=threading.RLock(),
            _channel_list_lock=threading.RLock()
        )
        global _urllib_request
        if self.python_version == 2:
            _urllib_request = _urllib_request_2
        else:
            _urllib_request = _urllib_request_3

    def timeout(self, interval, func):
        def cb():
            time.sleep(interval)
            func()
        thread = threading.Thread(target=cb)
        thread.start()


    def _request_async( self, request, callback=None, error=None, single=False ) :
        global _urllib_request
        ## Build URL
        url = self.getUrl(request)
        if single is True:
            id = time.time()
            client = HTTPClient(url=url, urllib_func=_urllib_request, callback=None, error=None, id=id)
            with latest_sub_callback_lock:
                latest_sub_callback['id'] = id
                latest_sub_callback['callback'] = callback
                latest_sub_callback['error'] = error
        else:
            client = HTTPClient(url=url, urllib_func=_urllib_request, callback=callback, error=error)

        thread = threading.Thread(target=client.run)
        thread.start()
        def abort():
            client.cancel();
        return abort


    def _request_sync( self, request) :
        global _urllib_request
        ## Build URL
        url = self.getUrl(request)
        ## Send Request Expecting JSONP Response
        response = _urllib_request(url, timeout=320)
        try:
            resp_json = json.loads(response[0])
        except:
            return [0,"JSON Error"]

        if response[1] != 200 and 'status' in resp_json:
            return {'message' : resp_json['message'], 'payload' : resp_json['payload']}

        return resp_json


    def _request(self, request, callback=None, error=None, single=False):
        if callback is None:
            return self._request_sync(request)
        else:
            self._request_async(request, callback, error, single=single)

'''

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
            '''
