Feature: Figma Design

  As a user
  I want the task manager to look and behave like the "Task management & to-do list app" design
  So that the app matches the intended product vision

  Scenario: The app uses the design's typography and colors
    Given the app is open
    Then the page uses the Manrope font family
    And the page uses the design's purple accent color
    And the page background is the design's light color

  Scenario: Home header shows today's progress
    Given I have existing tasks "Buy milk" and "Plan sprint"
    And "Buy milk" is completed
    Then the home header shows "Your today's task almost done!"
    And the home header shows the progress "50%"

  Scenario: Task groups summarize projects with counts and progress
    Given I have existing tasks "Buy milk" and "Plan sprint" in project "Office Project"
    And "Buy milk" is completed
    Then the task group "Office Project" shows "2" tasks
    And the task group "Office Project" shows "50%" progress

  Scenario: Filter chips filter the task board
    Given I have existing tasks "Buy milk" and "Plan sprint"
    And "Buy milk" is completed
    When I filter tasks by "Completed"
    Then the board shows "Buy milk"
    And the board does not show "Plan sprint"

  Scenario: Add a project from the Add Project form
    Given I open the Add Project form
    When I add a project named "Side Hustle"
    Then a task group "Side Hustle" appears on the home screen

  Scenario: New tasks belong to a project group
    Given I have existing tasks "Buy milk" and "Plan sprint" in project "Office Project"
    Then the task group "Office Project" shows "2" tasks
