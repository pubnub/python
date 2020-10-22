import pytest


@pytest.fixture()
def file_upload_test_data():
    return {
        "UPLOADED_FILENAME": "king_arthur.txt",
        "FILE_CONTENT": "Knights who say Ni!"
    }


@pytest.fixture
def file_for_upload(tmpdir, file_upload_test_data):
    temp_file = tmpdir.mkdir("fixutre").join(file_upload_test_data["UPLOADED_FILENAME"])
    temp_file.write(file_upload_test_data["FILE_CONTENT"])
    return temp_file


@pytest.fixture
def file_for_upload_10mb_size(tmpdir):
    temp_file = tmpdir.mkdir("fixutre").join("file_5mb")
    temp_file.write('0' * 10 * 1024 * 1024)
    return temp_file
