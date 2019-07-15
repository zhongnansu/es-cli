Feature: run the cli with args

  Scenario: run the cli with --query
    When we launch escli using --query
    Then we see query output


  # TODO: Add test case for other params