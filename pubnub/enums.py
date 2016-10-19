class HttpMethod(object):
    GET = 1
    POST = 2

    @classmethod
    def string(cls, method):
        if method == cls.GET:
            return "GET"
        elif method == cls.POST:
            return "POST"


class PNStatusCategory(object):
    PNUnknownCategory = 1
    PNAcknowledgmentCategory = 2
    PNAccessDeniedCategory = 3
    PNTimeoutCategory = 4
    PNNetworkIssuesCategory = 5
    PNConnectedCategory = 6
    PNReconnectedCategory = 7
    PNDisconnectedCategory = 8
    PNUnexpectedDisconnectCategory = 9
    PNCancelledCategory = 10
    PNBadRequestCategory = 11
    PNMalformedFilterExpressionCategory = 12
    PNMalformedResponseCategory = 13
    PNDecryptionErrorCategory = 14
    PNTLSConnectionFailedCategory = 15
    PNTLSUntrustedCertificateCategory = 16
    PNInternalExceptionCategory = 17


class PNOperationType(object):
    PNSubscribeOperation = 1
    PNUnsubscribeOperation = 2
    PNPublishOperation = 3
    PNHistoryOperation = 4
    PNWhereNowOperation = 5

    PNHeartbeatOperation = 6
    PNSetStateOperation = 7
    PNAddChannelsToGroupOperation = 8
    PNRemoveChannelsFromGroupOperation = 9
    PNChannelGroupsOperation = 10
    PNRemoveGroupOperation = 11
    PNChannelsForGroupOperation = 12
    PNPushNotificationEnabledChannelsOperation = 13
    PNAddPushNotificationsOnChannelsOperation = 14
    PNRemovePushNotificationsFromChannelsOperation = 15
    PNRemoveAllPushNotificationsOperation = 16
    PNTimeOperation = 17

    PNHereNowOperation = 18
    PNGetState = 19
    PNAccessManagerAudit = 20
    PNAccessManagerGrant = 21
    PNAccessManagerRevoke = 22


class PNHeartbeatNotificationOptions(object):
    NONE = 1
    FAILURES = 2
    ALL = 3


class PNReconnectionPolicy(object):
    NONE = 1
    LINEAR = 2
    EXPONENTIAL = 3


class PNPushType(object):
    APNS = 1
    MPNS = 2
    GCM = 3
