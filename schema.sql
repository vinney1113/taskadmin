CREATE TABLE IF NOT EXISTS projects (
  id           TEXT PRIMARY KEY,
  name         TEXT NOT NULL UNIQUE,
  icon         TEXT NOT NULL DEFAULT 'default',
  start_date   DATE,
  end_date     DATE,
  description  TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tasks (
  id          TEXT PRIMARY KEY,
  title       TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'prioritize',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  start_date  DATE,
  color       TEXT NOT NULL DEFAULT 'light',
  project_id  TEXT REFERENCES projects(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS tasks_project_id_idx ON tasks (project_id);
