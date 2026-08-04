Feature: Kanban Dashboard

  As a user
  I want to view and organize my tasks in a kanban board
  So that I can prioritize, start, and complete my work in columns

  Scenario: New tasks appear in the Prioritize column
    When I create a task "Plan sprint"
    Then the task "Plan sprint" is in the Prioritize column

  Scenario: Existing incomplete tasks appear in the Prioritize column
    Given I have an existing task "Buy milk"
    Then the task "Buy milk" is in the Prioritize column

  Scenario: The board always shows three columns
    Then the board shows the columns "Prioritize", "In Progress", and "Completed"

  Scenario: Move a task to In Progress
    Given I have an existing task "Buy milk"
    When I move the task "Buy milk" to "In Progress"
    Then the task "Buy milk" is in the In Progress column
    And the task "Buy milk" is not in the Prioritize column

  Scenario: Move a task to Prioritize
    Given I have an existing task "Buy milk" in "In Progress"
    When I move the task "Buy milk" to "Prioritize"
    Then the task "Buy milk" is in the Prioritize column
    And the task "Buy milk" is not in the In Progress column

  Scenario: Completing a task moves it to the Completed column
    Given I have an existing task "Buy milk"
    When I mark "Buy milk" as completed
    Then the task "Buy milk" is in the Completed column

  Scenario: Unmarking completion moves a task out of the Completed column
    Given I have an existing task "Buy milk" that is completed
    When I unmark "Buy milk" as completed
    Then the task "Buy milk" is not in the Completed column

  Scenario: Editing a task keeps it in the same column
    Given I have an existing task "Buy milk"
    When I move the task "Buy milk" to "In Progress"
    And I edit the task "Buy milk" to "Buy oat milk"
    Then the task "Buy oat milk" is in the In Progress column

  Scenario: Deleting a task removes it from its column
    Given I have an existing task "Buy milk"
    When I delete the task "Buy milk"
    Then the Prioritize column does not show "Buy milk"
