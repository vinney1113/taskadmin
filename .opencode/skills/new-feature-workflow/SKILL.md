---
name: new-feature-workflow
description: Use when creating a new feature. Follows a strict workflow: create a branch, review existing Gherkin-style user stories in the specs folder, write or update a .feature file, generate a technical spec, get user review, then build, run, and write tests.
---

# New Feature Workflow

Use this workflow when the user asks to create or implement a new feature. Work through the steps in order and do not skip ahead.

## 1) Create a branch

- Create a dedicated git branch for the feature: `git checkout -b feature/<short-description>`.
- Use a short, descriptive branch name based on the feature.

## 2) Review existing Gherkin-style user stories

- Look for existing user stories in the `specs/` folder (`.feature` files, Gherkin format).
- Review the structure and style of existing stories, including the current `spec.md` technical specification, to understand conventions already in use.

## 3) Write or update the user story

- Decide whether the feature is an entirely new feature or an extension of an existing one.
  - **Entirely new feature**: generate a new `.feature` file in `specs/`.
  - **Extension of an existing feature**: update the existing `.feature` file instead of creating a duplicate.
- Write the user story in Gherkin:
  - `Feature:` block with `As a ... / I want to ... / So that ...` user story.
  - One or more `Scenario:` blocks covering the happy path and edge cases.
- Save or update the file in the `specs/` folder with a `.feature` extension, following the existing conventions found in step 2.

## 4) Generate the technical specification

- Based on the user story, generate a technical specification.
- Cover: overview, data model, UI/UX, validation, persistence, and anything else relevant to the change.
- Save it in the `specs/` folder as `spec.md` (update the existing one if present), following the format of the current spec.

## 5) Ask the user to review

- STOP here and ask the user to review the `.feature` user story and `spec.md` technical specification.
- Do NOT proceed to build, run, or write tests until the user has confirmed the plan.

## 6) Build

- Implement the feature in the application code.
- Follow the technical specification and the repo's existing code conventions.
- Ensure the implementation is consistent with existing patterns (libraries, structure, style).

## 7) Run

- Run the application to verify the feature works.
- For this repo: serve the static app locally (e.g., `python3 -m http.server`) and verify the feature behaves as specified.

## 8) Create tests from the user story

- Translate the scenarios in the user story into tests.
- For this repo: use the Gherkin-driven e2e setup (pytest-bdd + Selenium). Add scenarios to `e2e/features/taskadmin.feature` and step definitions to `e2e/tests/test_taskadmin.py` as needed.
- Run the e2e suite with: `e2e/.venv/bin/python -m pytest -v`
- See `AGENTS.md` for the full testing instructions.
