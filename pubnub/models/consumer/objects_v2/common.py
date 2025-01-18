"""
This module defines classes for handling inclusion fields in PubNub objects.

Classes:
    PNIncludes: Base class for managing field mappings and string representation of included fields.
    MembershipIncludes: Inherits from PNIncludes, manages inclusion fields specific to membership objects.
    MemberIncludes: Inherits from PNIncludes, manages inclusion fields specific to member objects.
"""


class PNIncludes:
    """
    Base class for specific include classes that handles field mapping for all child classes.

    Attributes
    ----------
    field_mapping : dict
        A dictionary that maps internal field names to their corresponding external representations.

    Methods
    -------
    __str__():
        Returns a string representation of the object, consisting of the mapped field names that have non-false values.
    """

    field_mapping = {
        'custom': 'custom',
        'status': 'status',
        'type': 'type',
        'total_count': 'totalCount',
        'channel': 'channel',
        'channel_id': 'channel.id',
        'channel_custom': 'channel.custom',
        'channel_type': 'channel.type',
        'channel_status': 'channel.status',
        'user': 'uuid',
        'user_id': 'uuid.id',
        'user_custom': 'uuid.custom',
        'user_type': 'uuid.type',
        'user_status': 'uuid.status',
    }

    def __str__(self):
        """String formated to be used in requests."""
        return ','.join([self.field_mapping[k] for k, v in self.__dict__.items() if v])


class MembershipIncludes(PNIncludes):
    """
    MembershipIncludes is a class used to define what can be included in the objects membership endpoints.

    Attributes
    ----------
    custom : bool
        Indicates whether custom data should be included in the response.
    status : bool
        Indicates whether the status should be included in the response.
    type : bool
        Indicates whether the type should be included in the response.
    total_count : bool
        Indicates whether the total count should be included in the response.
    channel : bool
        Indicates whether the channel information should be included in the response.
    channel_custom : bool
        Indicates whether custom data for the channel should be included in the response.
    channel_type : bool
        Indicates whether the type of the channel should be included in the response.
    channel_status : bool
        Indicates whether the status of the channel should be included in the response.

    Methods
    -------
    __init__(self, custom: bool = False, status: bool = False, type: bool = False,
             channel_type: bool = False, channel_status: bool = False)
    """
    def __init__(self, custom: bool = False, status: bool = False, type: bool = False,
                 total_count: bool = False, channel: bool = False, channel_custom: bool = False,
                 channel_type: bool = False, channel_status: bool = False):
        """
        Initialize the Membership values to include within the response. By default, no values are included.

        Parameters
        ----------
        custom : bool, optional
        status : bool, optional
        type : bool, optional
        total_count : bool, optional
        channel : bool, optional
        channel_custom : bool, optional
        channel_type : bool, optional
        channel_status : bool, optional
        """

        self.custom = custom
        self.status = status
        self.type = type
        self.total_count = total_count
        self.channel = channel
        self.channel_custom = channel_custom
        self.channel_type = channel_type
        self.channel_status = channel_status


class MemberIncludes(PNIncludes):
    """
    MemberIncludes is a class used to define the values to include within the response for members requests.

    Attributes
    ----------
    custom : bool
        Indicates whether custom data should be included in the response.
    status : bool
        Indicates whether the status should be included in the response.
    type : bool
        Indicates whether the type should be included in the response.
    total_count : bool
        Indicates whether the total count should be included in the response.
    user : bool
        Indicates whether the user id should be included in the response.
    user_custom : bool
        Indicates whether custom data defined for the user should be included in the response.
    user_type : bool
        Indicates whether the type of the user should be included in the response.
    user_status : bool
        Indicates whether the status of the user should be included in the response.
    """

    def __init__(self, custom: bool = False, status: bool = False, type: bool = False,
                 total_count: bool = False, user: bool = False, user_custom: bool = False,
                 user_type: bool = False, user_status: bool = False):
        """
        Initialize the Member values to include within the response. By default, no values are included.

        Parameters
        ----------
        custom : bool, optional
        status : bool, optional
        type : bool, optional
        total_count : bool, optional
        channel : bool, optional
        channel_custom : bool, optional
        channel_type : bool, optional
        channel_status : bool, optional
        """

        self.custom = custom
        self.status = status
        self.type = type
        self.total_count = total_count
        self.user = user
        self.user_custom = user_custom
        self.user_type = user_type
        self.user_status = user_status
