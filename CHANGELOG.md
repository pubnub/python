
## [v3.8.3](https://github.com/pubnub/python/tree/v3.8.3)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.8.2...v3.8.3)


- ⭐Removing PubNub connection handling from using the global directive to allow multiple instances to run.



## [v3.8.2](https://github.com/pubnub/python/tree/v3.8.2)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.8.1...v3.8.2)


- ⭐Increasing maximum pool of connections and adjusting cryptodome package dependency.



## [v3.8.1](https://github.com/pubnub/python/tree/v3.8.1)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.8.0...v3.8.1)



- 🐛Fixing bug with state setting and subscribe confirmation.


## [v3.8.0](https://github.com/pubnub/python/tree/v3.8.0)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.7.7...v3.8.0)

- 🌟Mobile Gateway Functions.



- 🌟Here Now for channel groups.



- 🌟no-rep, store and fire().




## [v3.7.7](https://github.com/pubnub/python/tree/v3.7.7)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.7.6...v3.7.7)


- ⭐Adding .stop() method for base python async operations to exit the listener.



## [v3.7.6](https://github.com/pubnub/python/tree/v3.7.6)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.7.5...v3.7.6)



- 🐛fixed issues in receiving gzipped response for twisted.



- 🐛fix for non reporting of dns lookup failure.



- 🐛fix in time method.


## [v3.7.5](https://github.com/pubnub/python/tree/v3.7.5)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.7.4...v3.7.5)


- ⭐increased timeout to 15 sec.



## [v3.7.4](https://github.com/pubnub/python/tree/v3.7.4)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.7.2...v3.7.4)



- 🐛added state and here_now.

- 🌟added presence heartbeat support.




## [v3.7.2](https://github.com/pubnub/python/tree/v3.7.2)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.7.0...v3.7.2)



- 🐛fix for decryption bug in history API.


- ⭐module name changed to pubnub ( it was Pubnub earlier ), developers need to do from pubnub import Pubnub, instead of from Pubnub import Pubnub now.




- 🐛fixed method arguments bug for presence API.


- ⭐subscribe_sync removed.




- 🐛fix for issue where error callback not invoked for presence.

- 🌟added state support in subscribe and here now.





- 🐛fix for grant API with python 3.

- 🌟added include_token option to history.




## [v3.7.0](https://github.com/pubnub/python/tree/v3.7.0)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.5.3...v3.7.0)

- 🌟Channel Groups functionality.




- ⭐Added Python Echo Server example.




- 🐛Added missing timeout keyword arg.


## [v3.5.3](https://github.com/pubnub/python/tree/v3.5.3)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.5.2...v3.5.3)



- 🐛Added patch to handle quick net calls in Azure environments.



- 🐛Presence fixes.



- 🐛added daemon flag.


## [v3.5.2](https://github.com/pubnub/python/tree/v3.5.2)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.5.1...v3.5.2)

- 🌟Added pnsdk URL param to each request.




- ⭐Added grant/revoke/audit examples to README.




- 🐛Fixed erroneous "Connected" error condition in console.


- ⭐Can now pass init vars via the CL on console.




- 🐛Fixed UI issue of bracket color on console.


- ⭐Enable subscribing to "-pnpres" channel on console.



## [v3.5.1](https://github.com/pubnub/python/tree/v3.5.1)


  [Full Changelog](https://github.com/pubnub/python/compare/v3.5.0...v3.5.1)

- 🌟Added subscribe_sync method.




- ⭐renamed pres_uuid argument for Pubnub constructor to uuid.



## [v3.5.0](https://github.com/pubnub/python/tree/v3.5.0)



- 🌟Async subscribe allows for MX, unsubscribe calls.




- ⭐New method signatures -- be sure to check migration doc if upgrading.


