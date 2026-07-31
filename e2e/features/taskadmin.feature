Feature: Task Management

  As a user
  I want to manage my tasks
  So that I can create, list, and edit them

  Scenario: Edit a task title
    Given I have an existing task "Buy milk"
    When I edit the task "Buy milk" to "Buy almond milk"
    Then the task list should show "Buy almond milk"
    And the task list should not show "Buy milk"

  Scenario: Editing with an empty title is rejected
    Given I have an existing task "Buy milk"
    When I edit the task "Buy milk" to ""
    Then an error message is shown
    And the task title remains "Buy milk"

  Scenario: Editing preserves creation date, completion state, and start date
    Given I have an existing task "Buy milk" with start date "2026-08-03"
    When I mark "Buy milk" as completed
    And I edit the task "Buy milk" to "Buy milk and eggs"
    Then the task list shows "Buy milk and eggs"
    And the task "Buy milk and eggs" remains completed
    And the task "Buy milk and eggs" keeps its original creation date
    And the task "Buy milk and eggs" keeps its start date "2026-08-03"

  Scenario: Create a task with a start date
    Given I enter the task title "Plan sprint"
    And I set the start date to "2026-08-03"
    When I submit the task
    Then the task list shows "Plan sprint"
    And the task "Plan sprint" shows start date "2026-08-03"

  Scenario: Create a task without a start date
    Given I enter the task title "Quick note"
    And I leave the start date empty
    When I submit the task
    Then the task list shows "Quick note"
    And the task "Quick note" has no start date

  Scenario: Each task is assigned a unique color
    Given I have existing tasks "Buy milk" and "Plan sprint"
    When I create a task "Call plumber"
    Then the task "Call plumber" is assigned a color
    And the task "Buy milk" keeps its color
    And the task "Plan sprint" keeps its color
    And no two tasks share the same color

  Scenario: Editing preserves a task's color
    Given I have an existing task "Buy milk"
    When I edit the task "Buy milk" to "Buy almond milk"
    Then the task "Buy almond milk" keeps its original color

