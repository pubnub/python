from pubnub.endpoints.file_operations.get_file_url import GetFileDownloadUrl
from tests.helper import pnconf_file_copy
from pubnub.pubnub import PubNub


pubnub = PubNub(pnconf_file_copy())
pubnub.config.uuid = "killer_rabbit"


def test_get_complete_get_complete_url_for_file_download():
    file_download_url = GetFileDownloadUrl(pubnub).\
        channel("always_look_at_the_bright_side_of_life").\
        file_id(22222).\
        file_name("the_mightiest_tree").get_complete_url()

    assert "the_mightiest_tree" in file_download_url
    assert "always_look_at_the_bright_side_of_life" in file_download_url
    assert "killer_rabbit" in file_download_url
