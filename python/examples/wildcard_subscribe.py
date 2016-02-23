from gevent import monkey
from pubnub import Pubnub

monkey.patch_all()


pubnub = Pubnub(publish_key="ds", subscribe_key="ds",
                secret_key="ds", ssl_on=False)


# Wildcard Subscribe without presence

def a():
    channel_wc = "a.*"
    channel = "a.b"

    def callback(message1, channel1, real_channel=None):
        print(channel1 + " : " + real_channel + " : " + str(message1))

    def error(message):
        print("ERROR : " + str(message))

    def connect(channel1=None):
        print("Connect on " + channel1)
        print(pubnub.publish(channel=channel, message="a"))

    def disconnect(channel1=None):
        print("Disconnect on " + channel1)

    def reconnect(channel1=None):
        print("Reconnect on " + channel1)

    pubnub.subscribe(channels=channel_wc, callback=callback, error=callback,
                     connect=connect, disconnect=disconnect, reconnect=reconnect)


# Wildcard Subscribe with presence

def b():
    channel_wc = "b.*"
    channel = "b.c"

    def callback(message1, channel1, real_channel=None):
        print(channel1 + " : " + real_channel + " : " + str(message1))

    def error(message):
        print("ERROR : " + str(message))

    def presence(message1, channel1, real_channel=None):
        print(channel1 + " : " + real_channel + " : " + str(message1))

    def connect(channel1=None):
        print("Connect on " + channel1)
        print(pubnub.publish(channel=channel, message="b"))

    def disconnect(channel1=None):
        print("Disconnect on " + channel1)

    def reconnect(channel1=None):
        print("Reconnect on " + channel1)

    pubnub.subscribe(channels=channel_wc, callback=callback, error=callback,
                     connect=connect, disconnect=disconnect, reconnect=reconnect, presence=presence)


# Wildcard Subscribe and unsubscribe

def c():
    channel_wc = "c.*"
    channel = "c.d"

    def callback(message1, channel1, real_channel=None):
        print(channel1 + " : " + real_channel + " : " + str(message1))
        pubnub.unsubscribe(channel="c.*")
        print(pubnub.publish(channel=channel, message="c1"))

    def error(message):
        print("ERROR : " + str(message))

    def connect(channel1=None):
        print("Connect on " + channel1)
        print(pubnub.publish(channel=channel, message="c"))

    def disconnect(channel1=None):
        print("Disconnect on " + channel1)

    def reconnect(channel1=None):
        print("Reconnect on " + channel1)

    pubnub.subscribe(channels=channel_wc, callback=callback, error=callback,
                     connect=connect, disconnect=disconnect, reconnect=reconnect)


a()
b()
c()
