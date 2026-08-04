# Technical Specification — Kanban Dashboard

## Overview

The Kanban Dashboard is a feature of Vinay's Task Manager that organizes tasks into a three-column board: **Prioritize**, **In Progress**, and **Completed**. It replaces the app's flat task list. Tasks are moved between columns by dragging them (HTML5 drag-and-drop). Persists data in `localStorage`; no server or build step required.

## Data Model

The kanban feature extends the existing task model with a `status` field:

```
Task {
  id:        string    (UUID v4 via crypto.randomUUID(), timestamp fallback)
  title:     string    (required, max 255 chars)
  completed: boolean   (derived from status; kept in sync for backwards compatibility)
  status:    string    ("prioritize" | "in-progress" | "completed", default: "prioritize")
  createdAt: string    (ISO-8601 timestamp)
  startDate: string    (YYYY-MM-DD, optional)
  color:     string    (Bootstrap text-bg-* class name, e.g. "primary"; auto-assigned, unique among tasks)
}
```

## UI / UX

### Board layout

- The board renders all tasks from `localStorage` as cards grouped into three columns:

  | Column       | data-column   | Contains tasks with status |
  | ------------ | ------------- | -------------------------- |
  | Prioritize   | `prioritize`  | `prioritize`               |
  | In Progress  | `in-progress` | `in-progress`              |
  | Completed    | `completed`   | `completed`                |

- Columns use Bootstrap's responsive grid (`col-12 col-md-4`) so they stack on small screens and sit side by side on larger ones.
- Each column has a heading and lists its task cards as Bootstrap `list-group` items.
- The board always shows all three columns, even when a column is empty.

### Task cards

- Each card shows a completion checkbox, the title (struck through when completed), creation date, start date (if set), an Edit button, and a Delete button.
- New tasks are created with status `prioritize` and appear in the Prioritize column.
- Existing tasks without a `status` are migrated on load (`completed: true` → `completed`, otherwise → `prioritize`).

### Moving tasks

- Each card is draggable (`draggable="true"`). Dragging a card onto another column sets its `status` to that column and re-renders the board.
- Checking the completion checkbox sets status to `completed`; unchecking it sets status to `in-progress`.
- Visual feedback: cards show a grab cursor, dim while being dragged, and the column under the pointer is highlighted with a dashed outline.

### Edit and Delete

- Editing behaves as before; a task keeps its current column when its title changes.
- Deleting removes the task from its column.

## Persistence

- All tasks stored under the `tasks` key in `localStorage` as a JSON array.
- **Migration:** tasks written by older versions lack a `status`. On load, missing statuses are derived from the legacy `completed` field. The `completed` boolean is kept in sync with `status` on every save so storage remains backwards compatible.

## Validation

- Title must be non-empty (client-side check on submit).
- Start date, if provided, must be a valid `YYYY-MM-DD` date.

## Directory Structure

The kanban feature lives alongside the other specs and the app:

```
/
├── specs/
│   ├── start/          # Base task manager feature
│   │   ├── taskadmin.feature
│   │   └── spec.md
│   └── kanban/         # Kanban dashboard feature
│       ├── kanban.feature
│       └── spec.md
├── index.html          # Main HTML page (three-column board)
├── styles.css          # Minimal custom overrides on top of Bootstrap
├── app.js              # All application logic (status, migration, drag-and-drop)
├── vendor/             # Vendored Bootstrap CSS (self-hosted, no CDN)
└── e2e/                # Gherkin-driven end-to-end tests (pytest-bdd + Selenium)
```

## E2E Testing

- The kanban scenarios live in `specs/kanban/kanban.feature` (Gherkin), the single source of truth for this feature. The e2e suite loads them via `scenarios()` in `e2e/tests/test_taskadmin.py`, which also holds the step definitions.
- Scenarios cover: new and existing tasks landing in Prioritize, moving between columns by dragging, moving via the completion checkbox, keeping column on edit, and removing on delete.
- Drag-and-drop is simulated in Selenium by dispatching native `DragEvent`s with a `DataTransfer` object (HTML5 native drag events do not fire from Selenium's synthetic pointer actions).
- Selenium drives the system Chromium (`chromium`/`chromedriver` via apk) against a local `http.server` started by the test fixtures.
- Run with: `e2e/.venv/bin/python -m pytest -v`
- CI/CD: GitHub Actions (`.github/workflows/ci.yml`) runs the e2e suite on `ubuntu-latest` using Chrome for Testing and a matching chromedriver (via `browser-actions/setup-chrome`). It deploys to GitHub Pages only when the tests pass on `main`.
