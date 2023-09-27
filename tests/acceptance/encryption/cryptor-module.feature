@featureSet=cryptoModule @beta
Feature: Crypto module
  As a PubNub user
  I want to be able to encrypt data using crypto module
  I want to be able to decrypt data generated by previous cryptors

  Scenario Outline: AES-CBC cryptor data header can be processed
    Given Crypto module with 'acrh' cryptor
    * with '<cipher_key>' cipher key
    When I decrypt '<file>' file
    Then I receive '<outcome>'

    Examples:
      |  cipher_key  |              file              |        outcome        |
      # File without header can't be processed by crypto module (it doesn't have
      # legacy cryptor registered).
      | pubnubenigma | file-legacy-civ.jpg            | unknown cryptor error |
      # File without version can't be processed by specific new cryptor.
      | pubnubenigma | file-cryptor-no-version.txt    | decryption error      |
      # File with header which has unknown version
      | pubnubenigma | file-cryptor-unknown-acrh.jpg  | unknown cryptor error |
      # File with header which has too short identifier can't be processed.
      | pubnubenigma | file-cryptor-v1-short.txt      | decryption error      |
      # File with header with cryptor identifier not registered in crypto module
      # can't be processed.
      | pubnubenigma | file-cryptor-v1-unknown.txt    | unknown cryptor error |
      | pubnubenigma | file-cryptor-v1-acrh.jpg       | success               |
      | pubnubenigma | empty-file-cryptor-v1-acrh.txt | success               |

  Scenario Outline: Data encrypted with legacy AES-CBC cryptor is decryptable with legacy implementation
    Given Crypto module with 'legacy' cryptor
    Given Legacy code with '<cipher_key>' cipher key and '<vector>' vector
    * with '<cipher_key>' cipher key
    * with '<vector>' vector
    When I encrypt '<file>' file as 'binary'
    Then Successfully decrypt an encrypted file with legacy code

    Examples:
      |  cipher_key  |  vector  |      file      |
      | pubnubenigma | random   | file.jpg       |
      | pubnubenigma | constant | file.jpg       |
      | pubnubenigma | random   | file.txt       |
      | pubnubenigma | constant | file.txt       |
      | pubnubenigma | random   | empty-file.txt |
      | pubnubenigma | constant | empty-file.txt |

  # Stream-based encryption may not be supported by all platforms so it has been moved to the
  # separate scenario with ability to opt-out.
  Scenario Outline: Stream data encrypted with legacy AES-CBC cryptor is decryptable with legacy implementation
    Given Crypto module with 'legacy' cryptor
    Given Legacy code with '<cipher_key>' cipher key and '<vector>' vector
    * with '<cipher_key>' cipher key
    * with '<vector>' vector
    When I encrypt '<file>' file as 'stream'
    Then Successfully decrypt an encrypted file with legacy code

    Examples:
      |  cipher_key  | vector |      file      |
      | pubnubenigma | random | file.jpg       |
      | pubnubenigma | random | file.txt       |
      | pubnubenigma | random | empty-file.txt |

    Scenario Outline: Cryptor is able to process sample files as binary
      Given Crypto module with '<cryptor_id>' cryptor
      * with '<cipher_key>' cipher key
      * with '<vector>' vector
      When I decrypt '<encrypted_file>' file as 'binary'
      Then Decrypted file content equal to the '<source_file>' file content

      Examples:
        | cryptor_id |  cipher_key  |  vector  |          encrypted_file           |  source_file   |
        | legacy     | pubnubenigma | constant | file-cryptor-legacy-civ.jpg       | file.jpg       |
        | legacy     | pubnubenigma | random   | file-cryptor-legacy-riv.jpg       | file.jpg       |
        | legacy     | pubnubenigma | constant | file-cryptor-legacy-civ.txt       | file.txt       |
        | legacy     | pubnubenigma | random   | file-cryptor-legacy-riv.txt       | file.txt       |
        | legacy     | pubnubenigma | constant | empty-file-cryptor-legacy-civ.txt | empty-file.txt |
        | legacy     | pubnubenigma | random   | empty-file-cryptor-legacy-riv.txt | empty-file.txt |
        | legacy     | pubnubenigma | constant | file-legacy-civ.jpg               | file.jpg       |
        | legacy     | pubnubenigma | random   | file-legacy-riv.jpg               | file.jpg       |
        | legacy     | pubnubenigma | constant | file-legacy-civ.txt               | file.txt       |
        | legacy     | pubnubenigma | random   | file-legacy-riv.txt               | file.txt       |
        | legacy     | pubnubenigma | constant | empty-file-legacy-civ.txt         | empty-file.txt |
        | legacy     | pubnubenigma | random   | empty-file-legacy-riv.txt         | empty-file.txt |
        | acrh       | pubnubenigma | -        | file-cryptor-v1-acrh.jpg          | file.jpg       |
        | acrh       | pubnubenigma | -        | file-cryptor-v1-acrh.txt          | file.txt       |
        | acrh       | pubnubenigma | -        | empty-file-cryptor-v1-acrh.txt    | empty-file.txt |

    # Stream-based decryption may not be supported by all platforms so it has been moved to the
    # separate scenario with ability to opt-out.
    Scenario Outline: Cryptor is able to process sample files as stream
      Given Crypto module with '<cryptor_id>' cryptor
      * with '<cipher_key>' cipher key
      * with '<vector>' vector
      When I decrypt '<encrypted_file>' file as 'stream'
      Then Decrypted file content equal to the '<source_file>' file content

      Examples:
        | cryptor_id |  cipher_key  |  vector  |          encrypted_file           |  source_file   |
        | legacy     | pubnubenigma | random   | file-cryptor-legacy-riv.jpg       | file.jpg       |
        | legacy     | pubnubenigma | random   | file-cryptor-legacy-riv.txt       | file.txt       |
        | legacy     | pubnubenigma | random   | empty-file-cryptor-legacy-riv.txt | empty-file.txt |
        | legacy     | pubnubenigma | random   | file-legacy-riv.jpg               | file.jpg       |
        | legacy     | pubnubenigma | random   | file-legacy-riv.txt               | file.txt       |
        | legacy     | pubnubenigma | random   | empty-file-legacy-riv.txt         | empty-file.txt |
        | acrh       | pubnubenigma | -        | file-cryptor-v1-acrh.jpg          | file.jpg       |
        | acrh       | pubnubenigma | -        | file-cryptor-v1-acrh.txt          | file.txt       |
        | acrh       | pubnubenigma | -        | empty-file-cryptor-v1-acrh.txt    | empty-file.txt |

    Scenario Outline: Crypto module can handle encrypted data from different cryptors
      Given Crypto module with default '<cryptor_id1>' and additional '<cryptor_id2>' cryptors
      * with '<cipher_key>' cipher key
      * with '<vector>' vector
      When I decrypt '<encrypted_file>' file as 'binary'
      Then Decrypted file content equal to the '<source_file>' file content

      Examples:
        | cryptor_id1 | cryptor_id2 |  cipher_key  |  vector  |          encrypted_file           |  source_file   |
        | legacy      | acrh        | pubnubenigma | constant | file-cryptor-legacy-civ.jpg       | file.jpg       |
        | acrh        | legacy      | pubnubenigma | random   | file-legacy-riv.jpg               | file.jpg       |
        | legacy      | acrh        | pubnubenigma | constant | empty-file-cryptor-legacy-civ.txt | empty-file.txt |
        | acrh        | legacy      | pubnubenigma | random   | empty-file-legacy-riv.txt         | empty-file.txt |