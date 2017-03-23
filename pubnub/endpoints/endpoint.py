from abc import ABCMeta, abstractmethod

from pubnub import utils
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.errors import PNERR_SUBSCRIBE_KEY_MISSING, PNERR_PUBLISH_KEY_MISSING, PNERR_CHANNEL_OR_GROUP_MISSING, \
    PNERR_SECRET_KEY_MISSING, PNERR_CHANNEL_MISSING
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pn_error_data import PNErrorData
from ..structures import RequestOptions, ResponseInfo


class Endpoint(object):
    SERVER_RESPONSE_SUCCESS = 200
    SERVER_RESPONSE_FORBIDDEN = 403
    SERVER_RESPONSE_BAD_REQUEST = 400

    __metaclass__ = ABCMeta

    def __init__(self, pubnub):
        self.pubnub = pubnub
        self._cancellation_event = None
        self._sort_params = False

    def cancellation_event(self, event):
        self._cancellation_event = event
        return self

    @abstractmethod
    def build_path(self):
        pass

    @abstractmethod
    def custom_params(self):
        raise NotImplementedError

    def build_data(self):
        return None

    @abstractmethod
    def http_method(self):
        pass

    @abstractmethod
    def validate_params(self):
        pass

    @abstractmethod
    def create_response(self, endpoint):
        pass

    @abstractmethod
    def operation_type(self):
        raise NotImplementedError

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def request_timeout(self):
        pass

    @abstractmethod
    def connect_timeout(self):
        pass

    def is_auth_required(self):
        raise NotImplementedError

    def affected_channels(self):
        return None

    def affected_channels_groups(self):
        return None

    def options(self):
        return RequestOptions(
            path=self.build_path(),
            params_callback=self.build_params_callback(),
            method=self.http_method(),
            request_timeout=self.request_timeout(),
            connect_timeout=self.connect_timeout(),
            create_response=self.create_response,
            create_status=self.create_status,
            create_exception=self.create_exception,
            operation_type=self.operation_type(),
            data=self.build_data(),
            sort_arguments=self._sort_params)

    def sync(self):
        self.validate_params()

        envelope = self.pubnub.request_sync(self.options())

        if envelope.status.is_error():
            raise envelope.status.error_data.exception

        return envelope

    def async(self, callback):
        try:
            self.validate_params()
            options = self.options()
        except PubNubException as e:
            callback(None, self.create_status(PNStatusCategory.PNBadRequestCategory, None, None, e))
            return

        def callback_wrapper(envelope):
            callback(envelope.result, envelope.status)

        return self.pubnub.request_async(endpoint_name=self.name(),
                                         endpoint_call_options=options,
                                         callback=callback_wrapper,
                                         # REVIEW: include self._cancellation_event into options?
                                         cancellation_event=self._cancellation_event)

    def result(self):
        def handler():
            self.validate_params()
            return self.options()

        return self.pubnub.request_result(options_func=handler,
                                          cancellation_event=self._cancellation_event)

    def future(self):
        def handler():
            self.validate_params()
            return self.options()

        return self.pubnub.request_future(options_func=handler,
                                          cancellation_event=self._cancellation_event)

    def deferred(self):
        def handler():
            self.validate_params()
            return self.options()

        return self.pubnub.request_deferred(options_func=handler,
                                            cancellation_event=self._cancellation_event)

    def build_params_callback(self):
        def callback(params_to_merge):
            operation_type = self.operation_type()
            custom_params = self.custom_params()
            custom_params.update(params_to_merge)

            custom_params['pnsdk'] = self.pubnub.sdk_name
            custom_params['uuid'] = self.pubnub.uuid

            if self.is_auth_required() and self.pubnub.config.auth_key is not None:
                custom_params['auth'] = self.pubnub.config.auth_key

            if self.pubnub.config.secret_key is not None:
                custom_params['timestamp'] = str(self.pubnub.timestamp())
                signed_input = (self.pubnub.config.subscribe_key + "\n" + self.pubnub.config.publish_key + "\n")

                if operation_type == PNOperationType.PNAccessManagerAudit:
                    signed_input += 'audit\n'
                elif operation_type == PNOperationType.PNAccessManagerGrant or \
                        operation_type == PNOperationType.PNAccessManagerRevoke:
                    signed_input += 'grant\n'
                else:
                    signed_input += self.build_path() + "\n"

                signed_input += utils.prepare_pam_arguments(custom_params)
                signature = utils.sign_sha256(self.pubnub.config.secret_key, signed_input)

                custom_params['signature'] = signature

            # REVIEW: add encoder map to not hardcode encoding here
            if operation_type == PNOperationType.PNPublishOperation and 'meta' in custom_params:
                custom_params['meta'] = utils.url_encode(custom_params['meta'])
            if operation_type == PNOperationType.PNSetStateOperation and 'state' in custom_params:
                custom_params['state'] = utils.url_encode(custom_params['state'])

            # reassign since pnsdk should be signed unencoded
            custom_params['pnsdk'] = utils.url_encode(self.pubnub.sdk_name)

            return custom_params

        return callback

    def validate_subscribe_key(self):
        if self.pubnub.config.subscribe_key is None or len(self.pubnub.config.subscribe_key) == 0:
            raise PubNubException(pn_error=PNERR_SUBSCRIBE_KEY_MISSING)

    def validate_secret_key(self):
        if self.pubnub.config.secret_key is None or len(self.pubnub.config.secret_key) == 0:
            raise PubNubException(pn_error=PNERR_SECRET_KEY_MISSING)

    def validate_channel(self):
        if self._channel is None or len(self._channel) is 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_MISSING)

    def validate_channels_and_groups(self):
        if len(self._channels) == 0 and len(self._groups) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_OR_GROUP_MISSING)

    def validate_publish_key(self):
        if self.pubnub.config.publish_key is None or len(self.pubnub.config.publish_key) == 0:
            raise PubNubException(pn_error=PNERR_PUBLISH_KEY_MISSING)

    def create_status(self, category, response, response_info, exception):
        if response_info is not None:
            assert isinstance(response_info, ResponseInfo)

        pn_status = PNStatus()

        if response is None or exception is not None:
            pn_status.error = True

        if response is not None:
            pn_status.original_response = response

        if exception is not None:
            pn_status.error_data = PNErrorData(str(exception), exception)

        if response_info is not None:
            pn_status.status_code = response_info.status_code
            pn_status.tls_enabled = response_info.tls_enabled
            pn_status.origin = response_info.origin
            pn_status.uuid = response_info.uuid
            pn_status.auth_key = response_info.auth_key
            pn_status.client_request = response_info.client_request
            pn_status.client_response = response_info.client_response

        pn_status.operation = self.operation_type()
        pn_status.category = category
        pn_status.affected_channels = self.affected_channels()
        pn_status.affected_channels_groups = self.affected_channels_groups()

        return pn_status

    """ Used by asyncio and tornado clients to build exceptions

    The only difference with create_status() method is that a status
    is wrapped with an exception and also contains this exception inside
    as 'status.error_data.exception'
    """

    def create_exception(self, category, response, response_info, exception):
        status = self.create_status(category, response, response_info, exception)

        exception.status = status

        return exception
