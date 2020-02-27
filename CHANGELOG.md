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


