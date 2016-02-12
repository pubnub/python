# www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

# PubNub Real-time Push APIs and Notifications Framework
# Copyright (c) 2010 Stephen Blum
# http://www.pubnub.com/


import time
import random
from pubnub import Pubnub
from inspect import currentframe, getouterframes
from gevent import monkey

monkey.patch_all()


def get_line():
    # print getouterframes(currentframe())[3]
    return getouterframes(currentframe())[2][2]


DELAY = 5

RESULTS = {}


def check_tests():
    for i in RESULTS:
        test = RESULTS[i]
        if test['done'] is False:
            if test['expect'] == test['passed']:
                green(i + " PASSED " + str(test['passed']))
            else:
                red(i + " FAILED " + str(test['failed']))
            test['done'] = True


def init(conf, name, expect):
    # check_tests()
    print("\n\n")
    RESULTS[name + conf] = {'passed': 0, 'failed': 0, 'expect': 0, 'done': False, 'conf': conf}
    RESULTS[name + conf]['expect'] = expect


def get_random():
    return str(random.randint(1, 99999))


def red(name):
    print '\033[1;31m' + name + '\033[1;m'


def green(name):
    print '\033[1;92m' + name + '\033[1;m'


def test(cond, desc=None, test_name=None, conf=None):
    if (cond):
        green("[" + test_name + " " + conf + " ""][" + str(get_line()) + "] PASS : " + str(desc))
        RESULTS[test_name + conf]['passed'] = RESULTS[test_name + conf]['passed'] + 1
    else:
        red("[" + test_name + " " + conf + " ""][" + str(get_line()) + "] FAIL : " + str(desc))
        RESULTS[test_name + conf]['failed'] = RESULTS[test_name + conf]['failed'] + 1
        # exit(0)


def run_tests(tests):
    for test in tests:
        if len(test) > 4:
            test[1](test[2], test[3], test[0], test[4])
        else:
            test[1](test[2], test[3], test[0])
        time.sleep(DELAY)
        check_tests()


def test_1(pubnub, pubnub2, conf=None, msg=None):
    init(conf, "test_1", 6)
    r = get_random()
    channel_wc = r + "-" + "test_1-ab.*"
    message = msg if msg is not None else (r + "-" + "test_1_hi")
    channel = r + "-" + "test_1-ab.d"

    # Asynchronous usage
    def callback(message1, channel1, real_channel=None):
        # print(str(message1) + ' : ' + str(channel1) + ' : ' + str(real_channel))
        test(message1 == unicode(message, 'utf-8'), "message received", "test_1", conf)
        test(channel1 == channel_wc, "Channel == wildcard channel", "test_1", conf)
        test(real_channel == channel, "Real channel == publish channel", "test_1", conf)

    def error(message):
        print("ERROR : " + str(message))

    def connect(channel1=None):
        test(True, "Connect Called", "test_1", conf)
        test(channel1 == channel_wc, "Channel param in Connect same as wildcard", "test_1", conf)

        def _callback(message):
            test(message[0] == 1, "Publish Successful", "test_1", conf)

        def _error(message):
            test(False, "Publish Successful", "test_1", conf)

        pubnub.publish(channel=channel, message=message, callback=_callback, error=_error)

    pubnub.subscribe(channels=channel_wc, callback=callback, error=callback, connect=connect)


def test_2(pubnub, pubnub2, conf=None, msg=None):
    init(conf, "test_2", 8)
    r = get_random()
    channel_wc = r + "-" + "test_2-ab.*"
    message = msg if msg is not None else (r + "-" + "test_2_hi")
    channel = r + "-" + "test_2-ab.d"

    # Asynchronous usage
    def callback(message1, channel1, real_channel=None):
        # print(str(message1) + ' : ' + str(channel1) + ' : ' + str(real_channel))
        test(message1 == unicode(message, 'utf-8'), "message received", "test_2", conf)
        test(channel1 == channel_wc, "Channel == wildcard channel", "test_2", conf)
        test(real_channel == channel, "Real channel == publish channel", "test_2", conf)

    def error(message):
        print("ERROR : " + str(message))

    def presence(message, channel1, real_channel=None):
        if (pubnub.uuid == message['uuid']):
            test(channel_wc == real_channel, "On pubnub subscribe presence event as wildcard as real channel", "test_2",
                 conf)
        elif (pubnub2.uuid == message['uuid']):
            test(channel == real_channel, "On pubnub2 subscribe presence event as channel as real channel", "test_2",
                 conf)
        else:
            test(False, "Wrong presence event", "test_2", conf)

    def connect(channel1=None):
        # print(channel1)
        test(True, "Connect Called", "test_2", conf)
        test(channel1 == channel_wc, "Channel param in Connect same as wildcard", "test_2", conf)

        def _callback(message):
            test(message[0] == 1, "Publish Successful", "test_2", conf)

        def _error(message):
            test(False, "Publish Successful", "test_2", conf)

        pubnub.publish(channel=channel, message=message, callback=_callback, error=_error)

        def _callback(message, channel1):
            pass

        def _error(message):
            test(False, "Error in subscribe", "test_2", conf)

        pubnub2.subscribe(channels=channel, callback=_callback, error=_error)

    pubnub.subscribe(channels=channel_wc, callback=callback, error=callback, connect=connect, presence=presence)


def test_3(pubnub, pubnub2, conf=None, msg=None):
    init(conf, "test_3", 6)

    r = get_random()
    channel_wc = r + "-" + "test_3-ab.*"
    message = msg if msg is not None else (r + "-" + "test_3_hi")
    channel = r + "-" + "test_3-ab.d"

    # Asynchronous usage
    def callback(message1, channel1, real_channel=None):
        if 'action' in message1:
            test(False, "Presence event received without presence callback", "test_3", conf)
            return

        test(message1 == unicode(message, 'utf-8'), "message received", "test_3", conf)
        test(channel1 == channel_wc, "Channel == wildcard channel", "test_3", conf)
        test(real_channel == channel, "Real channel == publish channel", "test_3", conf)

    def error(message):
        print("ERROR : " + str(message))

    def connect(channel1=None):
        # print(channel1)
        test(True, "Connect Called", "test_3", conf)
        test(channel1 == channel_wc, "Channel param in Connect same as wildcard", "test_3", conf)

        def _callback(message):
            test(message[0] == 1, "Publish Successful", "test_3", conf)

        def _error(message):
            test(False, "Publish Successful", "test_3", conf)

        pubnub.publish(channel=channel, message=message, callback=_callback, error=_error)

        def _callback(message, channel1):
            pass

        def _error(message):
            test(False, "Error in subscribe", "test_3", conf)

        pubnub2.subscribe(channels=channel, callback=_callback, error=_error)

    pubnub.subscribe(channels=channel_wc, callback=callback, error=callback, connect=connect)


def test_4(pubnub, pubnub2, conf=None, msg=None):
    init(conf, "test_4", 18)

    r = get_random()
    channel_wc = r + "-" + "test_4-ab.*"
    channel_group = r + "-" + "test_4_group"
    channel_g = r + "-" + "test_4_group_channel"
    message = msg if msg is not None else (r + "-" + "test_4_hi")
    channel = r + "-" + "test_4-ab.d"
    channel_n = r + "-" + "test_4-a"

    def _callback(resp):
        # Asynchronous usage
        def callback_wc(message1, channel1, real_channel=None):
            test(message1 == unicode(message, 'utf-8'), "message received", "test_4", conf)
            test(channel1 == channel_wc, "Channel == wildcard channel", "test_4", conf)
            test(real_channel == channel, "Real channel == publish channel", "test_4", conf)

        def callback_group(message1, channel1, real_channel=None):
            test(message1 == unicode(message, 'utf-8'), "message received", "test_4", conf)
            test(channel1 == channel_group, "Channel == group", "test_4", conf)
            test(real_channel == channel_g, "Real channel == publish channel", "test_4", conf)

        def callback_n(message1, channel1, real_channel=None):
            test(message1 == unicode(message, 'utf-8'), "message received", "test_4", conf)
            test(channel1 == channel_n, "Channel ==  channel", "test_4", conf)
            test(real_channel == channel_n, "Real channel == publish channel", "test_4", conf)

        def error(message):
            print("ERROR : " + str(message))

        def connect_wc(channel1=None):
            test(True, "Connect Called", "test_4", conf)
            test(channel1 == channel_wc, "Channel param in Connect same as wildcard", "test_4", conf)

            def _callback(message):
                test(message[0] == 1, "Publish Successful", "test_4", conf)

            def _error(message):
                test(False, "Publish Successful", "test_4", conf)

            pubnub.publish(channel=channel, message=message, callback=_callback, error=_error)

        def connect_group(channel1=None):
            # print(channel1)
            test(True, "Connect Called", "test_4", conf)
            test(channel1 == channel_group, "Channel param in Connect same as channel_group", "test_4", conf)

            def _callback(message):
                test(message[0] == 1, "Publish Successful", "test_4", conf)

            def _error(message):
                test(False, "Publish Successful", "test_4", conf)

            pubnub.publish(channel=channel_g, message=message, callback=_callback, error=_error)

        def connect_n(channel1=None):
            # print(channel1)
            test(True, "Connect Called", "test_4", conf)
            test(channel1 == channel_n, "Channel param in Connect same as channel_n", "test_4", conf)

            def _callback(message):
                test(message[0] == 1, "Publish Successful", "test_4", conf)

            def _error(message):
                test(False, "Publish Successful", "test_4", conf)

            pubnub.publish(channel=channel_n, message=message, callback=_callback, error=_error)

        pubnub.subscribe(channels=channel_wc, callback=callback_wc, error=error, connect=connect_wc)

        pubnub.subscribe(channels=channel_n, callback=callback_n, error=error, connect=connect_n)

        pubnub.subscribe_group(channel_groups=[channel_group], callback=callback_group, error=error,
                               connect=connect_group)

    def _error(message):
        test(False, "Channel Group Creation failed")

    pubnub.channel_group_add_channel(channel_group=channel_group, channel=channel_g, callback=_callback, error=_error)


pubnub = Pubnub(publish_key="ds", subscribe_key="ds",
                secret_key="ds", ssl_on=False)

pubnub2 = Pubnub(publish_key="ds", subscribe_key="ds",
                 secret_key="ds", ssl_on=False)

pubnub_ssl = Pubnub(publish_key="ds", subscribe_key="ds",
                    secret_key="ds", ssl_on=True)

pubnub_ssl_2 = Pubnub(publish_key="ds", subscribe_key="ds",
                      secret_key="ds", ssl_on=True)

pubnub_enc = Pubnub(publish_key="ds", subscribe_key="ds",
                    secret_key="ds", cipher_key="enigma", ssl_on=False)

pubnub_enc_2 = Pubnub(publish_key="ds", subscribe_key="ds",
                      secret_key="ds", cipher_key="enigma", ssl_on=False, daemon=False)

pubnub_enc_ssl = Pubnub(publish_key="ds", subscribe_key="ds",
                        secret_key="ds", cipher_key="enigma", ssl_on=False)

pubnub_enc_ssl_2 = Pubnub(publish_key="ds", subscribe_key="ds",
                          secret_key="ds", cipher_key="enigma", ssl_on=False, daemon=False)

# run_tests([	("[EMOJI][ENC]", test_4, pubnub_enc, pubnub_enc_2, "😀")])


run_tests([
    ("", test_1, pubnub, pubnub2),
    ("[SSL]", test_1, pubnub_ssl, pubnub_ssl_2),
    ("[ENC]", test_1, pubnub_enc, pubnub_enc_2),
    ("[SSL][ENC]", test_1, pubnub_enc_ssl, pubnub_enc_ssl_2),
    ("", test_2, pubnub, pubnub2),
    ("[SSL]", test_2, pubnub_ssl, pubnub_ssl_2),
    ("[ENC]", test_2, pubnub_enc, pubnub_enc_2),
    ("[SSL][ENC]", test_2, pubnub_enc_ssl, pubnub_enc_ssl_2),
    ("", test_3, pubnub, pubnub2),
    ("[SSL]", test_3, pubnub_ssl, pubnub_ssl_2),
    ("[ENC]", test_3, pubnub_enc, pubnub_enc_2),
    ("[SSL][ENC]", test_3, pubnub_enc_ssl, pubnub_enc_ssl_2),
    ("", test_3, pubnub, pubnub2),
    ("[SSL]", test_3, pubnub_ssl, pubnub_ssl_2),
    ("[ENC]", test_3, pubnub_enc, pubnub_enc_2),
    ("[SSL][ENC]", test_3, pubnub_enc_ssl, pubnub_enc_ssl_2),
    ("", test_4, pubnub, pubnub2),
    ("[SSL]", test_4, pubnub_ssl, pubnub_ssl_2),
    ("[ENC]", test_4, pubnub_enc, pubnub_enc_2),
    ("[SSL][ENC]", test_4, pubnub_enc_ssl, pubnub_enc_ssl_2),
    ("[EMOJI]", test_1, pubnub, pubnub2, "😀"),
    ("[SSL][EMOJI]", test_1, pubnub_ssl, pubnub_ssl_2, "😀"),
    ("[ENC][EMOJI]", test_1, pubnub_enc, pubnub_enc_2, "😀"),
    ("[SSL][ENC][EMOJI]", test_1, pubnub_enc_ssl, pubnub_enc_ssl_2, "😀"),
    ("[EMOJI]", test_2, pubnub, pubnub2, "😀"),
    ("[SSL][EMOJI]", test_2, pubnub_ssl, pubnub_ssl_2, "😀"),
    ("[ENC][EMOJI]", test_2, pubnub_enc, pubnub_enc_2, "😀"),
    ("[SSL][ENC][EMOJI]", test_2, pubnub_enc_ssl, pubnub_enc_ssl_2, "😀"),
    ("[EMOJI]", test_3, pubnub, pubnub2, "😀"),
    ("[SSL][EMOJI]", test_3, pubnub_ssl, pubnub_ssl_2, "😀"),
    ("[ENC][EMOJI]", test_3, pubnub_enc, pubnub_enc_2, "😀"),
    ("[SSL][ENC][EMOJI]", test_3, pubnub_enc_ssl, pubnub_enc_ssl_2, "😀"),
    ("[EMOJI]", test_3, pubnub, pubnub2, "😀"),
    ("[SSL][EMOJI]", test_3, pubnub_ssl, pubnub_ssl_2, "😀"),
    ("[ENC][EMOJI]", test_3, pubnub_enc, pubnub_enc_2, "😀"),
    ("[SSL][ENC][EMOJI]", test_3, pubnub_enc_ssl, pubnub_enc_ssl_2, "😀"),
    ("[EMOJI]", test_3, pubnub, pubnub2, "😀"),
    ("[SSL][EMOJI]", test_3, pubnub_ssl, pubnub_ssl_2, "😀"),
    ("[ENC][EMOJI]", test_3, pubnub_enc, pubnub_enc_2, "😀"),
    ("[SSL][ENC][EMOJI]", test_3, pubnub_enc_ssl, pubnub_enc_ssl_2, "😀"),
    ("[EMOJI]", test_4, pubnub, pubnub2, "😀"),
    ("[SSL][EMOJI]", test_4, pubnub_ssl, pubnub_ssl_2, "😀"),
    ("[ENC][EMOJI]", test_4, pubnub_enc, pubnub_enc_2, "😀"),
    ("[SSL][ENC][EMOJI]", test_4, pubnub_enc_ssl, pubnub_enc_ssl_2, "😀")
])
