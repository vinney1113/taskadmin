# Technical Specification — Task Manager (Static Web App)

## Overview

A client-only single-page application for creating and listing tasks. Persists data in `localStorage`. No server or build step required.

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

- Single HTML page, mobile-first responsive design.
- Two sections: a form to add a task, and a table/list showing all tasks.

### "Create a task" form

- A text input for the task title, a date input for the optional start date, and an "Add" button.
- On submit, validate that the title is non-empty and the start date is a valid date, create a task object, store it in `localStorage`, and re-render the list.

### "List all tasks" view

- Renders all tasks from `localStorage` in a simple table/ul.
- Each row shows the title, creation date, and start date (if set).

## Persistence

- All tasks stored under the `tasks` key in `localStorage` as a JSON array.

## Validation

- Title must be non-empty (client-side check on submit).
- Start date, if provided, must be a valid `YYYY-MM-DD` date.

## Directory Structure

```
/
├── index.html       # Main HTML page
├── styles.css       # Minimal styling
└── app.js           # All application logic
```

No dependencies. Open `index.html` in a browser to run.
