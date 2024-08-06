import os


from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration


config = PNConfiguration()
config.publish_key = os.environ.get('PUBLISH_KEY', 'demo')
config.subscribe_request_timeout = 10
config.subscribe_key = os.environ.get('PUBLISH_KEY', 'demo')
config.enable_subscribe = False
config.user_id = 'example'

channel = 'file-channel'
pubnub = PubNub(config)
sample_path = f"{os.getcwd()}/examples/native_sync/sample.gif"

with open(sample_path, 'rb') as sample_file:
    response = pubnub.send_file() \
        .channel(channel) \
        .file_name("sample.gif") \
        .message({"test_message": "test"}) \
        .file_object(sample_file) \
        .sync()

    print(f"Sent file: {response.result.name} with id: {response.result.file_id},"
          f" at timestamp: {response.result.timestamp}")

file_list_response = pubnub.list_files().channel(channel).sync()
print(f"Found {len(file_list_response.result.data)} files:")

for file_data in file_list_response.result.data:
    print(f"  {file_data['name']} with id: {file_data['id']}")
    ext = file_data['name'].replace('sample', '')

    download_url = pubnub.get_file_url() \
        .channel(channel) \
        .file_id(file_data['id']) \
        .file_name(file_data['name']) \
        .sync()
    print(f'  Download url: {download_url.result.file_url}')

    download_file = pubnub.download_file() \
        .channel(channel) \
        .file_id(file_data['id']) \
        .file_name(file_data['name']) \
        .sync()

    fw = open(f"{os.getcwd()}/examples/native_sync/out-{file_data['id']}{ext}", 'wb')
    fw.write(download_file.result.data)
    print(f"  file saved as {os.getcwd()}/examples/native_sync/out-{file_data['id']}{ext}\n")

    pubnub.delete_file() \
        .channel(channel) \
        .file_id(file_data['id']) \
        .file_name(file_data['name']) \
        .sync()
    print(' File deleted from storage')
