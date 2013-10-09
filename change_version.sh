find -name "Pubnub*py" | xargs sed -i "s/PubNub\ [0-9]\.[0-9]\.[0-9]/PubNub\ `cat VERSION`/g"
