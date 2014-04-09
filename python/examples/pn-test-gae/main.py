#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import time
from Pubnub import Pubnub

pubnub = Pubnub( publish_key='demo', subscribe_key='demo', ssl_on=False )
pubnub_enc = Pubnub( publish_key='demo', subscribe_key='demo', cipher_key='enigma', ssl_on=False )
channel = 'gae-test-channel-' + str(time.time())

class MainHandler(webapp2.RequestHandler):

    def get(self):
    	info = pubnub.publish({
    		'channel' : channel,
    		'message' : {
        	'some_text' : 'Hello my World'
    		}
		})
        info_enc = pubnub_enc.publish({
    		'channel' : channel,
    		'message' : {
        	'some_text' : 'Hello my World'
    		}
		})
        hn = pubnub.here_now({
            'channel' : channel
        })
        history = pubnub.detailedHistory({
            'channel' : channel
        })
        history_enc = pubnub_enc.detailedHistory({
            'channel' : channel
        })
        self.response.write('Message published to channel ' + channel + '<br>' + str(info))
        self.response.write('<br><br>')
        self.response.write('Encrypted message published to channel ' + channel + '<br>' + str(info_enc))
        self.response.write('<br><br>')
        self.response.write('Here now data for channel : '+ channel + '<br>' + str(hn))
        self.response.write('<br><br>')
        self.response.write('History for channel : '+ channel + '<br>' + str(history))
        self.response.write('<br><br>')
        self.response.write('History with decryption enabled for channel : '+ channel + '<br>' + str(history_enc))


app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
