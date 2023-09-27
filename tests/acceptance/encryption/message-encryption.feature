@featureSet=subscribe
Feature: Message encryption
  As a PubNub user
  I want to be able to receive and decrypt messages
  So I can send confidential information throught PubNub network

  @contract=messageEncryption @beta
  Scenario: Receiving an encrypted message with correct crypto key
    Given the crypto keyset
    When I subscribe
    Then I receive the message in my subscribe response

  @contract=messageEncryption @beta
  Scenario: Receiving an encrypted message with invalid crypto key
    Given the invalid-crypto keyset
    When I subscribe
    Then an error is thrown
