# Technical Specification — Vinay's Task Manager (Static Web App)

## Overview

A client-only single-page application for creating and listing tasks. Persists data in `localStorage`. No server or build step required. UI is styled with Bootstrap 5 (vendored locally in `vendor/`) with minimal custom CSS overrides.

## Data Model

```
Task {
  id:        string    (UUID v4 via crypto.randomUUID(), timestamp fallback)
  title:     string    (required, max 255 chars)
  completed: boolean   (default: false)
  createdAt: string    (ISO-8601 timestamp)
  startDate: string    (YYYY-MM-DD, optional)
  color:     string    (Bootstrap text-bg-* class name, e.g. "primary"; auto-assigned, unique among tasks)
}
```

## UI / UX

### Layout

- Single HTML page, mobile-first responsive design using Bootstrap's grid and utility classes.
- Two sections: a form to add a task, and a table/list showing all tasks.

### "Create a task" form

- A text input for the task title, a date input for the optional start date, and an "Add" button (Bootstrap `form-control`, `btn`, and `alert` classes).
- On submit, validate that the title is non-empty and the start date is a valid date, create a task object with a unique color, store it in `localStorage`, and re-render the list.

### "List all tasks" view

- Renders all tasks from `localStorage` in a Bootstrap `list-group`.
- Each row shows a completion checkbox, the title, creation date, start date (if set), an Edit button, and a Delete button.
- Checking the completion checkbox toggles `completed` and strikes through the title; it does not change the task's color, dates, or title.
- The Delete button removes the task from storage and re-renders the list.

### Task color

- Every task is assigned a `color` from Bootstrap's theme color palette (`primary`, `success`, `danger`, `warning`, `info`, `dark`) when created.
- Colors are auto-assigned so that no two tasks share the same color; if every palette color is in use, the assignment cycles back to the beginning.
- A task's color is applied to its list row using Bootstrap's `text-bg-*` color-and-background helper, which sets the row background and a contrasting foreground automatically. The color is preserved when the task is edited.

## Persistence

- All tasks stored under the `tasks` key in `localStorage` as a JSON array.

## Validation

- Title must be non-empty (client-side check on submit).
- Start date, if provided, must be a valid `YYYY-MM-DD` date.

## Directory Structure

```
/
├── index.html       # Main HTML page (loads local Bootstrap CSS)
├── styles.css       # Minimal custom overrides on top of Bootstrap
├── app.js           # All application logic
├── vendor/          # Vendored Bootstrap CSS (self-hosted, no CDN)
└── e2e/             # Gherkin-driven end-to-end tests (pytest-bdd + Selenium)
```

## E2E Testing

- Scenarios live in `e2e/features/taskadmin.feature` (Gherkin) with step definitions in `e2e/tests/test_taskadmin.py`.
- Selenium drives the system Chromium (`chromium`/`chromedriver` via apk) against a local `http.server` started by the test fixtures.
- Run with: `e2e/.venv/bin/python -m pytest -v`
- CI: GitHub Actions (`.github/workflows/e2e.yml`) runs the same suite on `ubuntu-latest` using Chrome for Testing and a matching chromedriver installed via `browser-actions/setup-chrome`.

## Dependencies

- Bootstrap 5.3 (CSS) vendored locally in `vendor/bootstrap.min.css`. No internet connection or CDN required.
