Feature: Tasks REST API

  As a developer
  I want a REST API backed by PostgreSQL for tasks and projects
  So that the task manager can persist data on a server instead of the browser

  Background:
    Given the API is running against an empty database

  Scenario: Create a task
    When I POST a task with title "Plan sprint"
    Then the response status is 201
    And the response task has title "Plan sprint"
    And the response task has status "prioritize"

  Scenario: List tasks
    Given a task "Plan sprint" exists
    And a task "Buy milk" exists
    When I GET the tasks
    Then the response status is 200
    And the response contains tasks "Plan sprint" and "Buy milk"

  Scenario: Read a single task
    Given a task "Plan sprint" exists
    When I GET that task
    Then the response status is 200
    And the response task has title "Plan sprint"

  Scenario: Read a missing task returns 404
    When I GET a task with id "does-not-exist"
    Then the response status is 404

  Scenario: Update a task
    Given a task "Plan sprint" exists
    When I PUT that task with title "Plan a sprint" and status "in-progress"
    Then the response status is 200
    And the response task has title "Plan a sprint"
    And the response task has status "in-progress"

  Scenario: Delete a task
    Given a task "Plan sprint" exists
    When I DELETE that task
    Then the response status is 204
    And GET the tasks does not include "Plan sprint"

  Scenario: Reject an empty task title
    When I POST a task with title ""
    Then the response status is 400

  Scenario: Reject an invalid task status
    When I POST a task with title "Plan sprint" and status "nonsense"
    Then the response status is 400

  Scenario: Create a project
    When I POST a project with name "Office Project"
    Then the response status is 201
    And the response project has name "Office Project"

  Scenario: Reject a duplicate project name
    Given a project "Office Project" exists
    When I POST a project with name "Office Project"
    Then the response status is 409

  Scenario: Delete a project unlinks its tasks
    Given a project "Office Project" exists
    And a task "Plan sprint" assigned to "Office Project" exists
    When I DELETE that project
    Then the response status is 204
    And the task "Plan sprint" has no project
