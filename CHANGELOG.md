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
