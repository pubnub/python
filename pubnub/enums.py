from enum import Enum


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


class PNStatusCategory(Enum):
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
    PNSubscriptionChangedCategory = 18
    PNConnectionErrorCategory = 19


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

    PNAccessManagerRevokeToken = 40
    PNAccessManagerGrantToken = 41

    PNAddMessageAction = 42
    PNGetMessageActions = 43
    PNDeleteMessageAction = 44
    PNFetchMessagesOperation = 45

    PNGetFilesAction = 46
    PNDeleteFileOperation = 47
    PNGetFileDownloadURLAction = 48
    PNFetchFileUploadS3DataAction = 49
    PNDownloadFileAction = 50
    PNSendFileAction = 51
    PNSendFileNotification = 52

    PNSetUuidMetadataOperation = 53
    PNGetUuidMetadataOperation = 54
    PNRemoveUuidMetadataOperation = 55
    PNGetAllUuidMetadataOperation = 56

    PNSetChannelMetadataOperation = 57
    PNGetChannelMetadataOperation = 58
    PNRemoveChannelMetadataOperation = 59
    PNGetAllChannelMetadataOperation = 60

    PNSetChannelMembersOperation = 61
    PNGetChannelMembersOperation = 62
    PNRemoveChannelMembersOperation = 63
    PNManageChannelMembersOperation = 64

    PNSetMembershipsOperation = 65
    PNGetMembershipsOperation = 66
    PNRemoveMembershipsOperation = 67
    PNManageMembershipsOperation = 68

    PNCreateSpaceOperation = 69
    PNUpdateSpaceOperation = 70
    PNFetchSpaceOperation = 71
    PNFetchSpacesOperation = 72
    PNRemoveSpaceOperation = 73

    PNCreateUserOperation = 74
    PNUpdateUserOperation = 75
    PNFetchUserOperation = 76
    PNFetchUsersOperation = 77
    PNRemoveUserOperation = 78

    PNAddUserSpacesOperation = 79
    PNAddSpaceUsersOperation = 80
    PNUpdateUserSpacesOperation = 81
    PNUpdateSpaceUsersOperation = 82
    PNRemoveUserSpacesOperation = 81
    PNRemoveSpaceUsersOperation = 82
    PNFetchUserMembershipsOperation = 85
    PNFetchSpaceMembershipsOperation = 86


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
    APNS2 = 4


class PNResourceType(object):
    CHANNEL = "channel"
    GROUP = "group"
    USER = "user"
    SPACE = "space"


class PNMatchType(object):
    RESOURCE = "resource"
    PATTERN = "pattern"


class PNPushEnvironment(object):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class PAMPermissions(Enum):
    READ = 1
    WRITE = 2
    MANAGE = 4
    DELETE = 8
    CREATE = 16
    GET = 32
    UPDATE = 64
    JOIN = 128
