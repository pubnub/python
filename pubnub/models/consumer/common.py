class PNStatus:
    def __init__(self):
        self.category = None
        self.error_data = None
        self.error = None

        self.status_code = None
        self.operation = None

        self.tls_enabled = None

        self.uuid = None
        self.auth_key = None
        self.origin = None
        self.client_request = None
        self.client_response = None
        self.original_response = None

        self.affected_channels = None
        self.affected_groups = None

    def is_error(self):
        return self.error is not None
