# Technical Specification — Vinay's Task Manager (Static Web App)

## Overview

A client-only single-page application for creating and listing tasks. Persists data in `localStorage`. No server or build step required. UI is styled with Bootstrap 5 (loaded via CDN) with minimal custom CSS overrides.

## Data Model

```
Task {
  id:        number    (Date.now() based)
  title:     string    (required, max 255 chars)
  completed: boolean   (default: false)
  createdAt: string    (ISO-8601 timestamp)
  startDate: string    (YYYY-MM-DD, optional)
}
```

## UI / UX

### Layout

- Single HTML page, mobile-first responsive design using Bootstrap's grid and utility classes.
- Two sections: a form to add a task, and a table/list showing all tasks.

### "Create a task" form

- A text input for the task title, a date input for the optional start date, and an "Add" button (Bootstrap `form-control`, `btn`, and `alert` classes).
- On submit, validate that the title is non-empty and the start date is a valid date, create a task object, store it in `localStorage`, and re-render the list.

### "List all tasks" view

- Renders all tasks from `localStorage` in a Bootstrap `list-group`.
- Each row shows the title, creation date, start date (if set), and an Edit button.

## Persistence

- All tasks stored under the `tasks` key in `localStorage` as a JSON array.

## Validation

- Title must be non-empty (client-side check on submit).
- Start date, if provided, must be a valid `YYYY-MM-DD` date.

## Directory Structure

```
/
├── index.html       # Main HTML page (loads Bootstrap CSS from CDN)
├── styles.css       # Minimal custom overrides on top of Bootstrap
└── app.js           # All application logic
```

## Dependencies

- Bootstrap 5.3 (CSS) loaded from the jsDelivr CDN. Requires an internet connection.
