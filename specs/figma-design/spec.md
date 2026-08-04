# Technical Specification — Figma Design

## Overview

The app is restyled to match the community design file **"Task management & to-do list app"** (Figma key `ZWgkNJnWJ1BWjM4gpvjtSK`). The design contributes three app screens: **home** (progress summary + task groups), **today's tasks** (status filter chips + task list), and **add project** (project creation form). This feature applies the design's visual language to the existing task manager and adds project grouping, status filtering, and a project-creation form, while keeping the kanban board and all existing behavior intact.

Reference design screens: `let's start` (`101:100`), `home` (`101:125`), `today's tasks` (`101:265`), `add project in task list` (`101:358`).

## Design Tokens

Derived from the Figma file (fills/text colors):

| Token        | Value     | Used for                          |
| ------------ | --------- | --------------------------------- |
| `--ink`      | `#24242C` | headings, primary text            |
| `--muted`    | `#6E6A7C` | secondary text, labels            |
| `--primary`  | `#5F33E1` | buttons, active chips, progress    |
| `--bg`       | `#F0F0F0` | page background                   |
| `--surface`  | `#FFFFFF` | cards, inputs                      |
| `--lavender` | `#F4F0FF` | highlights, active chip background |
| `--danger`   | `#FF7D53` | destructive actions               |

- Typography: **Manrope** (sans-serif), weights 400–800. Self-hosted (vendored `woff2`) like Bootstrap; no CDN dependency.
- Cards: `border-radius: 1rem` (matching the design's rounded rectangles), soft drop shadow.
- Primary CTA style matches the design's "Let's Start"/"Add Project" purple buttons.

## Data Model

### Project (new storage key `projects`)

```
Project {
  id:          string    (UUID v4 via crypto.randomUUID(), timestamp fallback)
  name:        string    (required, max 255 chars)
  icon:        string    (Bootstrap text-bg-* class or palette color for the group icon)
  startDate:   string    (YYYY-MM-DD, optional)
  endDate:     string    (YYYY-MM-DD, optional)
  description: string    (optional)
  createdAt:   string    (ISO-8601 timestamp)
}
```

- On first load, if `projects` is absent, seed the design's groups: **Office Project**, **Personal Project**, **Daily Study**.
- New projects created via the Add Project form are appended; duplicates by name are rejected.

### Task (extended)

The existing `Task` model gains one field:

```
Task {
  ...existing fields...
  projectId: string | null   (links the task to a Project; null = ungrouped)
}
```

- Existing tasks without `projectId` migrate to `null` (no rewrite required).
- Assigning a task to a project is done when the task is created (project picker on the add-task form); existing tasks keep whatever they have.

## UI / UX

### Page shell

- Page background uses `--bg`; body text uses `--ink`; all text set in Manrope.
- Existing bootstrap classes and selectors (`#task-list`, `.kanban-column`, `.kanban-heading`, `#task-form`, `#title`, `#start-date`, `#error`, `.edit-input`, `button[data-action]`, `.fw-medium`) are preserved so the kanban behavior and tests keep working.

### Home header

- Below the page title, a summary card matching the design's `home` screen:
  - Heading **"Your today's task almost done!"** (design text `101:140`).
  - An SVG progress ring showing the percentage of tasks completed (e.g. `50%`); design shows `85%`.
  - A **View Task** button (`101:142`) that scrolls to the task board.
  - A notification icon (decorative).

### Task Groups (projects)

- A **Task Groups** section (`101:162`) renders one card per project from the `projects` list:
  - A colored icon (design uses briefcase / user / book icons).
  - The project name.
  - The number of tasks in the project (e.g. "6").
  - A progress bar / percentage of that project's tasks completed.
- Ungrouped tasks are not counted in any group.

### Filter chips

- Above the board, pill chips matching the design's `today's tasks` screen: **All**, **To do**, **In Progress**, **Completed** (`101:300`–`101:303`).
- Selecting a chip filters the board cards by status (`to do` → `prioritize`, others map to existing statuses). "All" shows everything.
- The active chip uses the design's lavender background + purple text.

### Add Project form

- A button opens the design's `add project` form (`101:358`): fields **Project Name**, **Start Date**, **End Date**, **Description** (`101:374`–`101:377`), and an **Add Project** submit button (`101:382`).
- The logo/icon row is simplified to an auto-assigned color; "Change Logo" image upload is out of scope.
- Submitting validates and appends a project; the home Task Groups section updates immediately.

## Validation

- Project name must be non-empty (client-side check); duplicate names rejected with an error message.
- Start/end dates, if provided, must be valid `YYYY-MM-DD`; `endDate` must not be before `startDate`.
- Existing task validations (title required, start date format) are unchanged.

## Persistence

- Projects stored under `projects` in `localStorage` (JSON array).
- Tasks keep living under `tasks`; `projectId` is optional and additive.
- **Migration:** first load seeds the three default projects if the key is missing. Tasks never need migration for this feature.

## Out of Scope

- The `let's start` splash/onboarding screen and image assets (stock photos, illustration rectangles) are not recreated.
- Calendar widget, per-task times (e.g. "10:00 AM"), and logo upload are not implemented; task `startDate` is still shown on cards.
- Single-page app: no multi-screen routing; "View Task" scrolls to the board.

## Directory Structure

```
specs/figma-design/
├── figma-design.feature   # User story (source of truth for e2e scenarios)
└── spec.md                # This specification
```

## E2E Testing

- New scenarios live in `specs/figma-design/figma-design.feature` and are wired through `e2e/tests/test_taskadmin.py` via `scenarios(...)`.
- Step definitions are added for: design tokens (font, accent color, background), progress ring, task groups, filter chips, and the Add Project form.
- Existing kanban and edit scenarios must continue to pass unchanged.
- Run: `e2e/.venv/bin/python -m pytest -v`
