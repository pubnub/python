import logging
from fastapi import BackgroundTasks, FastAPI
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio
import pubnub as pn


app = FastAPI()

pnconfig = PNConfiguration()
pnconfig.publish_key = "demo"
pnconfig.subscribe_key = "demo"
pnconfig.uuid = "UUID-PUB"
CHANNEL = "the_guide"


pubnub = PubNubAsyncio(pnconfig)
pn.set_stream_logger('pubnub', logging.DEBUG)


async def write_notification(email: str, message=""):
    with open("/tmp/log.txt", mode="w") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)

    await pubnub.publish().channel(CHANNEL).message(email).future()


@app.get("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    return {"message": "Notification sent in the background"}


@app.on_event("shutdown")
async def stop_pubnub():
    print("Closing Application")
    await pubnub.stop()
