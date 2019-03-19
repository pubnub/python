from pubnub.enums import PNStatusCategory
from pubnub.pubnub_twisted import PubNubTwisted as PubNub
from pubnub.pnconfiguration import PNConfiguration
from twisted.internet import reactor
from pubnub.callbacks import SubscribeCallback


def main():
    pnconf = PNConfiguration()
    pnconf.subscribe_key = 'demo'
    pnconf.publish_key = 'demo'

    pubnub = PubNub(pnconf)

    def my_publish_callback(result, status):
        # Check whether request successfully completed or not
        if not status.is_error():
            envelope = result  # noqa
            pass  # Message successfully published to specified channel.
        else:
            pass  # Handle message publish error. Check 'category' property to find out possible issue
            # because of which request did fail.
            # Request can be resent using: [status retry];

    class MySubscribeCallback(SubscribeCallback):
        def presence(self, pubnub, presence):
            pass  # handle incoming presence data

        def status(self, pubnub, status):
            if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
                pass  # This event happens when radio / connectivity is lost

            elif status.category == PNStatusCategory.PNConnectedCategory:
                # Connect event. You can do stuff like publish, and know you'll get it.
                # Or just use the connected event to confirm you are subscribed for
                # UI / internal notifications, etc
                pubnub.publish().channel("awesome_channel").message("Hello!").pn_async(my_publish_callback),

            elif status.category == PNStatusCategory.PNReconnectedCategory:
                pass
                # Happens as part of our regular operation. This event happens when
                # radio / connectivity is lost, then regained.
            elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
                pass
                # Handle message decryption error. Probably client configured to
                # encrypt messages and on live data feed it received plain text.

        def message(self, pubnub, message):
            # Handle new message stored in message.message
            pass

    pubnub.add_listener(MySubscribeCallback())
    pubnub.subscribe().channels('awesome_channel').execute()

    reactor.callLater(30, pubnub.stop)  # stop reactor loop after 30 seconds

    pubnub.start()


if __name__ == '__main__':
    main()
