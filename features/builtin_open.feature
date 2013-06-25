Feature: Read mocked file's content through open
  In order to read a mocked file in a valid encoding
  As a programmer
  I want the read function to return valid value.

  Scenario: Create with byte string and no encoding
    Given I make a file with byte string "あいうえお" encoded with "utf8" and specify no encoding
     When I read its contents through __builtins__.open
     Then I get a value which is instance of str
      And it is encoded in "utf8"

  Scenario: Create with byte string and encoding
    Given I make a file with byte string "あいうえお" encoded with "utf8" and specify "utf8" encoding
     When I read its contents through __builtins__.open
     Then I get a value which is instance of str
      And it is encoded in "utf8"

  Scenario: Create with byte string and different encoding
    Given I make a file with byte string "あいうえお" encoded with "utf8" and specify "cp932" encoding
     Then I get an UnicodeDecodeError when reading its contents through __builtins__.open

  Scenario: Create with unicode and no encoding
    Given I make a file with unicode string "あいうえお" and specify no encoding
     When I read its contents through __builtins__.open
     Then I get a value which is instance of str
      And it is encoded in "utf8"

  Scenario: Create with unicode and encoding
    Given I make a file with unicode string "あいうえお" and specify "cp932" encoding
     When I read its contents through __builtins__.open
     Then I get a value which is instance of str
      And it is encoded in "cp932"

