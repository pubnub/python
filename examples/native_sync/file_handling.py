""" File handling example with PubNub

This example demonstrates how to integrate file handling with PubNub. Here, we will:
1. Upload a file to a specified channel.
2. List all files in that channel.
3. Get the download URL for each file.
4. Download each file and save it locally.
5. Delete each file from the channel.

Note: Ensure you have the necessary permissions and configurations set up in your PubNub account.
"""

import os
from typing import List
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration


# snippet.setup
def setup_pubnub() -> PubNub:
    """Set up PubNub configuration.
    This function initializes the PubNub instance with the necessary configuration.
    It retrieves the publish and subscribe keys from environment variables,
    or defaults to 'demo' if not set. Proper keyset can be obtained from PubNub admin dashboard.

    Returns:
        - PubNub: The PubNub instance with configuration.
    """
    config = PNConfiguration()
    config.publish_key = os.environ.get('PUBNUB_PUBLISH_KEY', 'demo')
    config.subscribe_key = os.environ.get('PUBNUB_SUBSCRIBE_KEY', 'demo')
    config.user_id = 'example'
    return PubNub(config)
# snippet.end


# snippet.uploading_files
def upload_file(pubnub: PubNub, channel: str, file_path: str) -> dict:
    """Upload a given file to PubNub.

    Args:
        - pubnub (PubNub): The PubNub instance.
        - channel (str): The channel to upload the file to.
        - file_path (str): The path to the file to upload.
    Returns:
        - str: The file ID of the uploaded file.
    """
    with open(file_path, 'rb') as sample_file:
        response = pubnub.send_file() \
            .channel(channel) \
            .file_name("sample.gif") \
            .message({"test_message": "test"}) \
            .file_object(sample_file) \
            .sync()
        return response.result
# snippet.end


# snippet.listing_files
def list_files(pubnub: PubNub, channel: str) -> List[dict]:
    """List all files in a channel.

    Calling list_files() will return a list of files in the specified channel. This list includes fields:
    - id: The unique identifier for the file. This id is used to download or delete the file.
    - name: The original name of the uploaded file.
    - size: The size of the file in bytes.
    - created: The timestamp when the file was created.

    Args:
        - pubnub (PubNub): The PubNub instance.
        - channel (str): The channel to list files from.
    Returns:
        - List[dict]: A list of files with their metadata.
    """
    file_list_response = pubnub.list_files().channel(channel).sync()
    return file_list_response.result.data
# snippet.end


# snippet.getting_the_download_url
def get_download_url(pubnub: PubNub, channel: str, file_id: str, file_name: str) -> str:

    """Get the download URL for a file.
    This method allows you to retrieve the download URL for a specific file in a channel.
    Each file has a unique, temporary URL that can be used to download the file.

    Args:
        - pubnub (PubNub): The PubNub instance.
        - channel (str): The channel where the file is stored.
        - file_id (str): The unique identifier of the file.
        - file_name (str): The name of the file.
    Returns:
        - str: The download URL for the file.
    """
    download_url = pubnub.get_file_url() \
        .channel(channel) \
        .file_id(file_id) \
        .file_name(file_name) \
        .sync()
    return download_url.result.file_url
# snippet.end


# snippet.downloading_files
def download_file(pubnub: PubNub, channel: str, file_id: str, file_name: str, dest_dir: str) -> str:
    """Download a file from a channel.

    This method allows you to download a file from a specified channel.
    The file is saved to the specified destination directory with the original file name.

    Args:
        - pubnub (PubNub): The PubNub instance.
        - channel (str): The channel to download the file from.
        - file_id (str): The unique identifier of the file.
        - file_name (str): The name of the file.
        - dest_dir (str): The directory where the file will be saved.
    Returns:
        - str: The file path where the downloaded file is saved.
    """
    download_file = pubnub.download_file() \
        .channel(channel) \
        .file_id(file_id) \
        .file_name(file_name) \
        .sync()
    output_file_path = f"{dest_dir}/{file_id}_{file_name}"
    with open(output_file_path, 'wb') as fw:
        fw.write(download_file.result.data)
    return output_file_path
# snippet.end


# snippet.deleting_files
def delete_file(pubnub: PubNub, channel: str, file_id: str, file_name: str) -> None:
    """Delete a file from a channel.

    Args:
        - pubnub (PubNub): The PubNub instance.
        - channel (str): The channel to delete the file from.
        - file_data (dict): The metadata of the file to delete.
    """
    pubnub.delete_file() \
        .channel(channel) \
        .file_id(file_id) \
        .file_name(file_name) \
        .sync()
# snippet.end


# snippet.basic_usage
def main():
    print("\n=== Starting File Handling Example ===")
    print("This example demonstrates how to upload, list, download, and delete files using PubNub.")
    print("Ensure you have the necessary permissions and configurations set up in your PubNub account.")

    pubnub = setup_pubnub()
    channel = "file_handling_channel"
    file_path = f"{os.path.dirname(__file__)}/sample.gif"
    downloads_path = f"{os.path.dirname(__file__)}/downloads"

    if not os.path.exists(downloads_path):
        os.makedirs(downloads_path)

    print(f"Using channel: {channel}")
    print(f"File path: {file_path}")
    print(f"Downloads path: {downloads_path}")

    # Upload a file
    uploaded_file = upload_file(pubnub, channel, file_path)
    # Making sure we uploaded file properly
    assert uploaded_file.file_id is not None, "File upload failed"
    assert uploaded_file.name == os.path.basename(file_path), "File upload failed"

    print(f"Sent file: {uploaded_file.name} with id: {uploaded_file.file_id}, at timestamp: {uploaded_file.timestamp}")

    # List files in the channel
    file_list = list_files(pubnub, channel)
    # Making sure we received file list
    assert len(file_list) > 0, "File list is empty"

    print(f"Found {len(file_list)} files:")
    for file_data in file_list:
        print(f"  {file_data['name']} with:\n"
              f"    id: {file_data['id']}\n"
              f"    size: {file_data['size']}\n"
              f"    created: {file_data['created']}\n")
        download_url = get_download_url(pubnub, channel, file_data['id'], file_data['name'])
        downloaded_file_path = download_file(pubnub, channel, file_data['id'], file_data['name'], downloads_path)
        assert download_url is not None, "Failed fetching download UR"
        assert os.path.exists(downloaded_file_path), "File download failed"

        print(f"    Download url: {download_url}")
        print(f"    Downloaded to: {downloaded_file_path}")

        # Delete files from the storage:
        delete_file(pubnub, channel, file_data['id'], file_data['name'])

    # snippet.hide
    if not os.getenv('CI'):
        input("Press any key to continue...")
    # snippet.show

    # Remove downloads path with all the files in it
    for root, _, files in os.walk(downloads_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))

    os.rmdir(downloads_path)
    print(f"Removed downloads directory: {downloads_path}")
# snippet.end


if __name__ == "__main__":
    main()
