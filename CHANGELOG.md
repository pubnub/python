## v9.1.0
November 19 2024

#### Added
- Publish, signal, share file, subscribe and history.

## v9.0.0
October 02 2024

#### Added
- BREAKING CHANGES: Automatic reconnecting for subscribe with exponential backoff is now enabled by default.
- Access manager v2 endpoints (grant and audit) will no longer be supported after December 31, 2024, and will be removed without further notice. Refer to the documentation to learn more.
- BREAKING CHANGES: Once used to instantiate PubNub, the configuration object (PNConfiguration instance) becomes immutable. You will receive exceptions if you rely on modifying the configuration after the PubNub instance is created. Refer to the documentation to learn more.

#### Modified
- Type hints for parameters and return values are now added to provide a better developer experience.
- All endpoints are now accessible through the builder pattern and named parameters, providing a more flexible experience suitable for custom solutions.

## v8.1.0
August 13 2024

#### Added
- Option to lock PNConfiguration mutability. Note that mutable config will be deprecated in future major releases.

#### Fixed
- Fix for routing crypto module if custom one was defined.

#### Modified
- Additional Examples.

## v8.0.0
May 09 2024

#### Added
- A new version of subscription and presence handling is enabled by default (enableEventEngine flag is set to true). Please consult the documentation for new PNStatus values that are emitted for subscriptions, as code changes might be required to support this change.
- Channels, ChannelGroups, ChannelMetadata and UserMetadata.

## v7.4.4
April 10 2024

#### Fixed
- Fix compatibility issues between EventEngine and Asyncio subscription manager.

## v7.4.3
March 28 2024

#### Fixed
- Fixes in the thread based subscription managers causing to duplicate subscription calls.

## v7.4.2
March 07 2024

#### Fixed
- Add missing status and type fields in app context. Now they are included, by default, in the response for getting channel/uuid metadata .

## v7.4.1
February 26 2024

#### Fixed
- Fixes AsyncioTelemetryManager to avoid creating a task every second.

## v7.4.0
February 08 2024

#### Added
- Optional Event Engine for Subscribe Loop.

## v7.3.2
November 27 2023

#### Fixed
- Gracefully handle decrypting an unencrypted method. If a decryption error occurs when trying to decrypt plain text, the plain text message will be returned and an error field will be set in the response. This works for both history and subscription messages.

## v7.3.1
October 30 2023

#### Fixed
- Changed license type from MIT to PubNub Software Development Kit License.

## v7.3.0
October 16 2023

#### Added
- Add crypto module that allows configure SDK to encrypt and decrypt messages.

#### Fixed
- Improved security of crypto implementation by adding enhanced AES-CBC cryptor.

## 7.2.0
July 06 2023

#### Added
- Introduced option to select ciphering method for encoding messages and files. The default behavior is unchanged. More can be read [in this comment](https://github.com/pubnub/python/pull/156#issuecomment-1623307799).

## 7.1.0
January 17 2023

#### Added
- Add optional TTL parameter for publish endpoint.

## 7.0.2
November 24 2022

#### Fixed
- This change fixes typo in consumer models user and space resulting in setting invalid flags for the request.
- This change fixes error in calling and returning value of `status.is_error()` method.
- This change adds additional informations to PyPi package. Informations include URLs to source code and documentation, required python version (at least 3.7) and updates a list of supported python versions (removed 3.6 and added 3.10). Fixed the following issues reported by [@Saluev](https://github.com/Saluev), [@natekspencer](https://github.com/natekspencer) and [@andriyor](https://github.com/andriyor): [#145](https://github.com/pubnub/python/issues/145), [#102](https://github.com/pubnub/python/issues/102) and [#115](https://github.com/pubnub/python/issues/115).

## 7.0.1
October 05 2022

#### Fixed
- Remove deprecation warning of Event.is_set and Thread.deamon.

## 7.0.0
August 23 2022

#### Modified
- Update build process to include python v3.10-dev and remove v3.6.
- Fix of randomly failing tests of `where_now feature`.

## v6.5.1
August 02 2022

#### Fixed
- Fix bugs in Spaces Membership endpoints.

## v6.5.0
July 27 2022

#### Added
- Grant token now supports Users and Spaces.

## v6.4.1
July 14 2022

#### Fixed
- This addresses the issue #130 - a problem with importing module.

## v6.4.0
July 13 2022

#### Added
- Spaces Users and Membership endpoint implementation. This functionality is hidden behind a feature flag. By default it is disabled. To enable it there should be an environment variable named `PN_ENABLE_ENTITIES` set to `True`.

## v6.3.3
June 25 2022

#### Fixed
- Fixed error which happened when random initialization vector has been used. Request path was encrypted two times, once to prepare signage and second one when sending the request.
- Fixed exception while receiving empty `message` field in `FileMessageResult`.

## v6.3.2
May 16 2022

#### Fixed
- Fix issue with signing objects requests containing filter.

## v6.3.1
April 27 2022

#### Fixed
- This issue was mentioned in issue #118 and replaces PR #119 to match our PR policy. Fixed the following issues reported by [@tjazsilovsek](https://github.com/tjazsilovsek) and [@tjazsilovsek](https://github.com/tjazsilovsek): [#118](https://github.com/pubnub/python/issues/118) and [#119](https://github.com/pubnub/python/issues/119).

## v6.3.0
April 01 2022

#### Added
- Add methods to include additional fields in fetch_messages.

## v6.2.0
March 21 2022

#### Added
- Add methods to change use compression option on chosen endpoints.

## v6.1.0
March 01 2022

#### Added
- Add config option to set Content-Encoding to 'gzip'.

## v6.0.1
February 01 2022

#### Fixed
- Remove unwanted output while calling `fetch_messages`.

## v6.0.0
January 13 2022

#### Modified
- BREAKING CHANGES: uuid is required parameter while creating an instance of PubNub.

## v5.5.0
December 16 2021

## [v5.5.0](https://github.com/pubnub/python/releases/tag/v5.5.0)  

- 🌟️ Revoke token functionality.

## v5.4.0
December 16 2021

## [v5.4.0](https://github.com/pubnub/python/releases/tag/v5.4.0)

[Full Changelog](https://github.com/pubnub/python/compare/v5.3.1...v5.4.0)

- 🌟️ Parse_token method refactored. 

## [v5.3.1](https://github.com/pubnub/python/releases/tag/v5.3.1)

[Full Changelog](https://github.com/pubnub/python/compare/v5.3.0...v5.3.1)

- 🌟️ Grant result object __str__ message unified. 

## [v5.3.0](https://github.com/pubnub/python/releases/tag/v5.3.0)

[Full Changelog](https://github.com/pubnub/python/compare/v5.2.1...v5.3.0)

- 🌟️ Extend grant_token method to enable control of Objects API permission. Enhance granularity of permission control to enable permissions per UUID.

## [v5.2.1](https://github.com/pubnub/python/releases/tag/v5.2.1)

[Full Changelog](https://github.com/pubnub/python/compare/v5.2.0...v5.2.1)

- 🐛 Encoding of the double quote character fixed.

## [v5.2.0](https://github.com/pubnub/python/releases/tag/v5.2.0)

[Full Changelog](https://github.com/pubnub/python/compare/v5.1.4...v5.2.0)

- 🌟️ PAMv3 support for Objects_v2 added (beta).
     Furthermore PAMv3 tokens can now be used within other PubNub features.

## [v5.1.4](https://github.com/pubnub/python/releases/tag/v5.1.4)

[Full Changelog](https://github.com/pubnub/python/compare/v5.1.3...v5.1.4)

- 🌟️ SDK metadata was added.
     Additionally, example code for the FastAPI integration was added.

## [v5.1.3](https://github.com/pubnub/python/releases/tag/v5.1.3)

[Full Changelog](https://github.com/pubnub/python/compare/v5.1.2...v5.1.3)

- 🐛 Disabling default request headers within the Endpoint.

## [v5.1.2](https://github.com/pubnub/python/releases/tag/v5.1.2)

[Full Changelog](https://github.com/pubnub/python/compare/v5.1.1...v5.1.2)

- 🐛 Request headers required by the Grant Token functionality added.

## [v5.1.1](https://github.com/pubnub/python/releases/tag/v5.1.1)

[Full Changelog](https://github.com/pubnub/python/compare/v5.1.0...v5.1.1)

- 🐛 Multiple community Pull Requests for Asyncio related code applied. 

## [v5.1.0](https://github.com/pubnub/python/releases/tag/v5.1.0)

[Full Changelog](https://github.com/pubnub/python/compare/v5.0.1...v5.1.0)

- 🌟️ BREAKING CHANGE: Add randomized initialization vector usage by default for data encryption / decryption in publish / subscribe / history API calls. 

## [v5.0.1](https://github.com/pubnub/python/releases/tag/v5.0.1)

[Full Changelog](https://github.com/pubnub/python/compare/v5.0.0...v5.0.1)

- 🌟️ User defined 'origin'(custom domain) value was not used in all required places within this SDK. 

## [v5.0.0](https://github.com/pubnub/python/releases/tag/v5.0.0)

[Full Changelog](https://github.com/pubnub/python/compare/v4.8.1...v5.0.0)

- ⭐️️ Support for Python 2.7 was removed, support for the contemporary versions of Python was added.
     Apart from bringing the whole SDK up to date, support for Tornado and Twisted was removed and dependencies were simplified. 

## [v4.8.1](https://github.com/pubnub/python/releases/tag/v4.8.1)

[Full Changelog](https://github.com/pubnub/python/compare/v4.8.0...v4.8.1)

- 🌟️ New v3 History endpoint allows to fetch 100 messages per channel. 

## [v4.8.0](https://github.com/pubnub/python/releases/tag/v4.8.0)

[Full Changelog](https://github.com/pubnub/python/compare/v4...v4.8.0)

- 🌟️ Objects v2 implementation added to the PythonSDK with additional improvements to the test isolation within whole test suite. 

## [v4.7.0](https://github.com/pubnub/python/releases/tag/v4.7.0)

[Full Changelog](https://github.com/pubnub/python/compare/v4.6.1...v4.7.0)

- 🐛 Within this release problems with double PAM calls encoding and Publish oriented bugs were fixed. 

## [v4.6.1](https://github.com/pubnub/python/releases/tag/v4.6.1)

[Full Changelog](https://github.com/pubnub/python/compare/v4.6.0...v4.6.1)

- 🐛 Passing uuid to the get_state endpoint call added. 

## [v4.6.0](https://github.com/pubnub/python/releases/tag/v4.6.0)

[Full Changelog](https://github.com/pubnub/python/compare/v4.5.4...v4.6.0)

- 🌟️ File Upload added to the Python SDK. 
- ⭐️️ Fix spelling typos in `.pubnub.yml` file. Addresses the following PRs from [@samiahmedsiddiqui](https://github.com/samiahmedsiddiqui): [#92](https://github.com/pubnub/python/pull/92).

## [v4.5.4](https://github.com/pubnub/python/releases/tag/v4.5.4)

[Full Changelog](https://github.com/pubnub/python/compare/v4.5.3...v4.5.4)

- 🌟️ Add `suppress_leave_events` configuration option which can be used to opt-out presence leave call on unsubscribe. 
- ⭐️️ Log out message decryption error and pass received message with `PNDecryptionErrorCategory` category to status listeners. 

## [v4.5.3](https://github.com/pubnub/python/releases/tag/v4.5.3)

[Full Changelog](https://github.com/pubnub/python/compare/v4.5.2...v4.5.3)

- ⭐️️ Allocating separate thread that basically waits certain amount of time to clean telemetry data is a waste of memory/OS data strucutres. Clening mentioned data can be incorporated into regular logic. 

## [v4.5.2](https://github.com/pubnub/python/releases/tag/v4.5.2)

[Full Changelog](https://github.com/pubnub/python/compare/v4.5.1...v4.5.2)

- 🐛 Fix bug with max message count parameter for Fetch Messages endpoint. Rename maximum_per_channel parameter to count for Fetch Messages, keeping the old name for compatibility. 

## [v4.5.1](https://github.com/pubnub/python/releases/tag/v4.5.1)

- 🐛 Using SSL by default from the Python SDK to be more consistent and encourage best practices. 

## [4.5.0](https://github.com/pubnub/python/tree/v4.5.0)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.4.0...v4.5.0)

- 🌟 Implemented Objects Filtering API

## [4.4.0](https://github.com/pubnub/python/tree/v4.4.0)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.3.0...v4.4.0)

- 🌟 Add support for APNS2 Push API

## [4.3.0](https://github.com/pubnub/python/tree/v4.3.0)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.2.1...v4.3.0)

- 🌟 Implemented Message Actions API
- 🌟 Implemented Fetch Messages API
- 🌟 Added 'include_meta' to history()
- 🌟 Added 'include_meta' to fetch_messages()
- 🌟 Added 'include_message_actions' to fetch_messages()

## [4.2.1](https://github.com/pubnub/python/tree/v4.2.1)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.2.0...v4.2.1)

- 🐛Excluded the tilde symbol from being encoded by the url_encode method to fix invalid PAM signature issue.

## [4.2.0](https://github.com/pubnub/python/tree/v4.2.0)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.1.7...v4.2.0)

- 🌟 Introduced delete permission to Grant endpoint. Migrated to v2 enpdoints for old PAM methods.
- 🌟 Added TokenManager and GrantToken method.
- 🌟Resolved warnings caused by the use of deprecated methods.
- 🐛Removed Audit tests.
- 🐛Resolved incorrectly reported SDK version.

## [4.1.7](https://github.com/pubnub/python/tree/v4.1.7)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.1.6...v4.1.7)

- 🌟Add users join, leave and timeout fields to interval event

## [4.1.6](https://github.com/pubnub/python/tree/v4.1.6)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.1.5...v4.1.6)

- 🐛implement Objects API

## [4.1.5](https://github.com/pubnub/python/tree/v4.1.5)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.1.4...v4.1.5)

- 🐛implement signal

## [4.1.4](https://github.com/pubnub/python/tree/v4.1.4)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.1.3...v4.1.4)

- 🐛implement fire

## [4.1.3](https://github.com/pubnub/python/tree/v4.1.3)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.1.2...v4.1.3)

- 🐛Implement history message counts

## [4.1.2](https://github.com/pubnub/python/tree/v4.1.2)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.1.1...v4.1.2)

- 🐛Rename await to pn_await

## [4.1.1](https://github.com/pubnub/python/tree/v4.1.1)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.1.0...v4.1.1)

- 🐛Rename async to pn_async


## [4.1.0](https://github.com/pubnub/python/tree/v4.1.0)

  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.12...v4.1.0)


- 🐛Add telemetry manager
- 🌟Fix plugins versions and remove unused plugins
- 🌟Add history delete


## [v4.0.12](https://github.com/pubnub/python/tree/v4.0.12)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.11...v4.0.12)



- 🐛Fixed issues with managing push notifications

## [v4.0.11](https://github.com/pubnub/python/tree/v4.0.11)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.10...v4.0.11)



- 🐛Fix typo on announce_status.


## [v4.0.10](https://github.com/pubnub/python/tree/v4.0.10)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.9...v4.0.10)



- 🐛Fix aiohttp v1.x.x and v2.x.x compatibility


## [v4.0.9](https://github.com/pubnub/python/tree/v4.0.9)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.8...v4.0.9)



- 🐛Fix missing encoder for path elements
- 🌟




## [v4.0.8](https://github.com/pubnub/python/tree/v4.0.8)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.7...v4.0.8)

- 🌟Support log_verbosity in pnconfiguration to enable HTTP logging.




## [v4.0.7](https://github.com/pubnub/python/tree/v4.0.7)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.6...v4.0.7)



- 🐛Handle interval presence messages gracefully if they do not contain a UUID.
- 🌟Support custom cryptography module when using GAE



- ⭐designate the request thread as non-daemon to keep the SDK running.



## [v4.0.6](https://github.com/pubnub/python/tree/v4.0.6)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.5...v4.0.6)



- 🐛Fix on state object type definition.


## [v4.0.5](https://github.com/pubnub/python/tree/v4.0.5)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.4...v4.0.5)


- ⭐new pubnub domain


- ⭐native demo app


- ⭐fixed HTTPAdapter config


- ⭐add a new Python 3.6.0 config to travis builds


- ⭐fix blocking Ctrl+C bug



## [v4.0.4](https://github.com/pubnub/python/tree/v4.0.4)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.3...v4.0.4)


- ⭐Add reconnection managers



## [v4.0.3](https://github.com/pubnub/python/tree/v4.0.3)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.2...v4.0.3)


- ⭐do not strip plus sign when encoding message.



## [v4.0.2](https://github.com/pubnub/python/tree/v4.0.2)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.1...v4.0.2)


- ⭐Adjusting maximum pool size for requests installations


- ⭐Adding Publsher UUID



## [v4.0.1](https://github.com/pubnub/python/tree/v4.0.1)


  [Full Changelog](https://github.com/pubnub/python/compare/v4.0.0...v4.0.1)


- ⭐Fixing up packaging configuration for py3



## [v4.0.0](https://github.com/pubnub/python/tree/v4.0.0)




- ⭐Initial Release
