import os


from pubnub.pubnub_asyncio import PubNubAsyncio
from pubnub.pnconfiguration import PNConfiguration


config = PNConfiguration()
config.publish_key = os.environ.get('PN_KEY_PUBLISH')
config.subscribe_request_timeout = 10
config.subscribe_key = os.environ.get('PN_KEY_SUBSCRIBE')
config.enable_subscribe = False
config.uuid = 'demo'

channel = 'file-channel'
pubnub = PubNubAsyncio(config)
sample_path = f"{os.getcwd()}/examples/native_sync/sample.gif"


def callback(response, *args):
    print(f"Sent file: {response.result.name} with id: {response.result.file_id},"
          f" at timestamp: {response.result.timestamp}")


with open(sample_path, 'rb') as sample_file:
    sample_file.seek(0)
    pubnub.send_file() \
        .channel(channel) \
        .file_name("sample.gif") \
        .message({"test_message": "test"}) \
        .file_object(sample_file) \
        .pn_async(callback)

file_list_response = pubnub.list_files().channel(channel).sync()
print(f"Found {len(file_list_response.result.data)} files:")

for pos in file_list_response.result.data:
    print(f"  {pos['name']} with id: {pos['id']}")
    ext = pos['name'].replace('sample', '')
    download_url = pubnub.get_file_url().channel(channel).file_id(pos['id']).file_name(pos['name']).sync()
    print(f'  Download url: {download_url.result.file_url}')
    download_file = pubnub.download_file().channel(channel).file_id(pos['id']).file_name(pos['name']).sync()
    fw = open(f"{os.getcwd()}/examples/native_sync/out-{pos['id']}{ext}", 'wb')
    fw.write(download_file.result.data)
    print(f"  file saved as {os.getcwd()}/examples/native_sync/out-{pos['id']}{ext}\n")
    pubnub.delete_file().channel(channel).file_id(pos['id']).file_name(pos['name']).sync()
    print(' File deleted from storage')
