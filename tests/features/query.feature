Feature: manipulate tables:
  select, delete
# TODO Add delete test if jdbc for deletion sql is fixed

  Scenario: select
      When we select from table
      Then we see data selected

