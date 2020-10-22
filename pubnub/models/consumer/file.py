class PNGetFilesResult:
    def __init__(self, result):
        self.data = result['data']
        self.count = result.get('count', None)
        self.next = result.get('next', None)
        self.prev = result.get('prev', None)

    def __str__(self):
        return "Get files success with data: %s" % self.data


class PNDeleteFileResult:
    def __init__(self, result):
        self.status = result['status']

    def __str__(self):
        return "Delete files success with status: %s" % self.status


class PNGetFileDownloadURLResult:
    def __init__(self, result, data=None):
        self.file_url = result.headers["Location"]

    def __str__(self):
        return "Get file URL success with status: %s" % self.status


class PNFetchFileUploadS3DataResult:
    def __init__(self, result):
        self.name = result["data"]["name"]
        self.file_id = result["data"]["id"]
        self.data = result["file_upload_request"]

    def __str__(self):
        return "Fetch file upload S3 data success with status: %s" % self.status


class PNDownloadFileResult:
    def __init__(self, result):
        self.data = result

    def __str__(self):
        return "Downloading file success with status: %s" % self.status


class PNSendFileResult:
    def __init__(self, result, file_upload_data):
        self.name = file_upload_data.result.name
        self.file_id = file_upload_data.result.file_id

    def __str__(self):
        return "Sending file success with status: %s" % self.status


class PNPublishFileMessageResult:
    def __init__(self, result):
        self.timestamp = result[2]

    def __str__(self):
        return "Sending file notification success with status: %s" % self.status
