## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.0 Real-time Push Cloud API
## -----------------------------------

import sys
from Pubnub import PubnubAsync as Pubnub
import unittest as unittest


publish_key = len(sys.argv) > 1 and sys.argv[1] or 'demo'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'demo'
secret_key = len(sys.argv) > 3 and sys.argv[3] or None
ssl_on = len(sys.argv) > 4 and bool(sys.argv[4]) or False
pubnub = Pubnub(publish_key, subscribe_key, secret_key, ssl_on)
crazy = ' ~`!@#$%^&*(顶顅Ȓ)+=[]\\{}|;\':",./<>?abcd'


class TestDetailedHistory(unittest.TestCase):
    total_msg = 10
    channel = pubnub.time()
    starttime = None
    inputs = []
    endtime = None
    slice_a = 8
    slice_b = 2
    slice_size = slice_a - slice_b

    @classmethod
    def publish_msg(cls, start, end, offset):
        print('Publishing messages')
        inputs = []
        for i in range(start + offset, end + offset):
            message = str(i) + " " + crazy
            success = pubnub.publish({
                                     'channel': cls.channel,
                                     'message': message,
                                     })
            t = pubnub.time()
            inputs.append({'timestamp': t, 'message': message})
            print(('Message # ' + i + ' published'))
        return inputs

    @classmethod
    def setUpClass(c):
        print('Setting up context for Detailed History tests. Please wait ...')
        c.starttime = pubnub.time()
        c.inputs = c.inputs + c.publish_msg(0, c.total_msg / 2, 0)
        c.midtime = pubnub.time()
        c.inputs = c.inputs + c.publish_msg(
            0, c.total_msg / 2, c.total_msg / 2)
        c.endtime = pubnub.time()
        print('Context setup for Detailed History tests. Now running tests')

    def test_begin_to_end_count(self):
        count = 5
        history = pubnub.detailedHistory({
                                         'channel': self.__class__.channel,
                                         'start': self.__class__.starttime,
                                         'end': self.__class__.endtime,
                                         'count': count
                                         })[0]
        self.assertTrue(len(history) == count and history[-1].encode(
            'utf-8') == self.__class__.inputs[count - 1]['message'])

    def test_end_to_begin_count(self):
        count = 5
        history = pubnub.detailedHistory({
                                         'channel': self.__class__.channel,
                                         'start': self.__class__.endtime,
                                         'end': self.__class__.starttime,
                                         'count': count
                                         })[0]
        self.assertTrue(len(history) == count and history[-1]
            .encode('utf-8') == self.__class__.inputs[-1]['message'])

    def test_start_reverse_true(self):
        history = pubnub.detailedHistory({
                                         'channel': self.__class__.channel,
                                         'start': self.__class__.midtime,
                                         'reverse': True
                                         })[0]
        self.assertTrue(len(history) == self.__class__.total_msg / 2)
        expected_msg = self.__class__.inputs[-1]['message']
        self.assertTrue(history[-1].encode('utf-8') == expected_msg)

    def test_start_reverse_false(self):
        history = pubnub.detailedHistory({
                                         'channel': self.__class__.channel,
                                         'start': self.__class__.midtime,
                                         })[0]
        self.assertTrue(history[0].encode('utf-8')
                        == self.__class__.inputs[0]['message'])

    def test_end_reverse_true(self):
        history = pubnub.detailedHistory({
                                         'channel': self.__class__.channel,
                                         'end': self.__class__.midtime,
                                         'reverse': True
                                         })[0]
        self.assertTrue(history[0].encode('utf-8')
                        == self.__class__.inputs[0]['message'])

    def test_end_reverse_false(self):
        history = pubnub.detailedHistory({
                                         'channel': self.__class__.channel,
                                         'end': self.__class__.midtime,
                                         })[0]
        self.assertTrue(len(history) == self.__class__.total_msg / 2)
        self.assertTrue(history[-1].encode('utf-8')
                        == self.__class__.inputs[-1]['message'])

    def test_count(self):
        history = pubnub.detailedHistory({
                                         'channel': self.__class__.channel,
                                         'count': 5
                                         })[0]
        self.assertTrue(len(history) == 5)

    def test_count_zero(self):
        history = pubnub.detailedHistory({
                                         'channel': self.__class__.channel,
                                         'count': 0
                                         })[0]
        self.assertTrue(len(history) == 0)

if __name__ == '__main__':
    unittest.main()
