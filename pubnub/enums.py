class HttpMethod(object):
    GET = 1
    POST = 2
    DELETE = 3
    PATCH = 4

    @classmethod
    def string(cls, method):
        if method == cls.GET:
            return "GET"
        elif method == cls.POST:
            return "POST"
        elif method == cls.DELETE:
            return "DELETE"
        elif method == cls.PATCH:
            return "PATCH"


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
    PNHistoryDeleteOperation = 23
    PNMessageCountOperation = 24
    PNFireOperation = 25
    PNSignalOperation = 26
    PNGetUsersOperation = 27
    PNCreateUserOperation = 28
    PNGetUserOperation = 29
    PNUpdateUserOperation = 30
    PNDeleteUserOperation = 31
    PNGetSpacesOperation = 32
    PNCreateSpaceOperation = 33
    PNGetSpaceOperation = 34
    PNUpdateSpaceOperation = 35
    PNDeleteSpaceOperation = 36
    PNGetMembersOperation = 37
    PNGetSpaceMembershipsOperation = 38
    PNManageMembersOperation = 39
    PNManageMembershipsOperation = 40


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
