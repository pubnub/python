# AsyncIO PubNub Subscribe Example

### Usage example:
```shell
pip install asyncio pubnub
export PUBNUB_PUBLISH_KEY=demo
export PUBNUB_SUBSCRIBE_KEY=demo
python main.py
```

### Output:
```
Listening for messages...
Connected
Received message: Hello World on channel: my_channel
Received message: Hello World on channel: my_channel
Received message: Hello World on channel: my_channel
Received message: Hello World on channel: my_channel
Received message: Hello World on channel: my_channel
```


### In another terminal:
```shell
export PUBNUB_PUBLISH_KEY=demo
export PUBNUB_SUBSCRIBE_KEY=demo
curl "https://ps.pndsn.com/publish/${PUBNUB_PUBLISH_KEY}/${PUBNUB_SUBSCRIBE_KEY}/0/my_channel/0/%22Hello%20World%22"
```

### Output:
```
[1,"Sent","17183967137027574"]
```
