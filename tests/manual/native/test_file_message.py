import logging
import os
import sys

d = os.path.dirname
PUBNUB_ROOT = d(d(d(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PUBNUB_ROOT)

from tests.helper import pnconf_file_copy
import pubnub as pn
from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub import PubNub

pn.set_stream_logger('pubnub', logging.DEBUG)
logger = logging.getLogger("file_upload")


class FileSubscribeCallback(SubscribeCallback):
    def message(self, pubnub, event):
        print("MESSAGE: ")
        print(event.message)

    def file(self, pubnub, event):
        print("FILE: ")
        print(event.message)
        print(event.file_url)
        print(event.file_name)
        print(event.file_id)


pubnub = PubNub(pnconf_file_copy())
pubnub.config.cipher_key = "silly_walk"

my_listener = FileSubscribeCallback()
pubnub.add_listener(my_listener)
pubnub.subscribe().channels("files_native_sync_ch").execute()
