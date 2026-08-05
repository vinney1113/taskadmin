const express = require('express');
const pool = require('../db');

const router = express.Router();

const STATUSES = new Set(['prioritize', 'in-progress', 'completed']);

const TASK_COLORS = ['primary', 'success', 'danger', 'warning', 'info', 'dark'];

function isDateString(value) {
  return (
    typeof value === 'string' &&
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(new Date(`${value}T00:00:00`).getTime())
  );
}

function toTask(row) {
  return {
    id: row.id,
    title: row.title,
    status: row.status,
    createdAt: new Date(row.created_at).toISOString(),
    startDate: row.start_date || null,
    color: row.color,
    projectId: row.project_id || null,
  };
}

const TASK_COLUMNS = `
  id, title, status, created_at,
  to_char(start_date, 'YYYY-MM-DD') AS start_date, color, project_id
`;

async function pickColor() {
  const { rows } = await pool.query('SELECT color FROM tasks');
  const used = new Set(rows.map((row) => row.color));
  const free = TASK_COLORS.filter((color) => !used.has(color));
  if (free.length > 0) return free[0];
  return TASK_COLORS[rows.length % TASK_COLORS.length];
}

function validateTaskBody(body, { requireTitle = false } = {}) {
  const errors = [];
  const fields = {};

  if (requireTitle || body.title !== undefined) {
    if (typeof body.title !== 'string' || !body.title.trim()) {
      errors.push('title is required and must not be empty');
    } else if (body.title.trim().length > 255) {
      errors.push('title must be 255 characters or fewer');
    } else {
      fields.title = body.title.trim();
    }
  }

  if (body.status !== undefined) {
    if (!STATUSES.has(body.status)) {
      errors.push('status must be one of: prioritize, in-progress, completed');
    } else {
      fields.status = body.status;
    }
  }

  if (body.startDate !== undefined) {
    if (body.startDate === null) {
      fields.start_date = null;
    } else if (!isDateString(body.startDate)) {
      errors.push('startDate must be a valid YYYY-MM-DD date');
    } else {
      fields.start_date = body.startDate;
    }
  }

  if (body.color !== undefined) {
    if (typeof body.color !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(body.color)) {
      errors.push('color must be a valid CSS class name');
    } else {
      fields.color = body.color;
    }
  }

  if (body.projectId !== undefined) {
    fields.project_id = body.projectId;
  }

  return { errors, fields };
}

async function ensureProject(projectId) {
  if (!projectId) return true;
  const { rowCount } = await pool.query('SELECT 1 FROM projects WHERE id = $1', [projectId]);
  return rowCount > 0;
}

router.get('/', async (req, res, next) => {
  try {
    const { rows } = await pool.query(
      `SELECT ${TASK_COLUMNS} FROM tasks ORDER BY created_at, id`
    );
    res.json(rows.map(toTask));
  } catch (err) {
    next(err);
  }
});

router.post('/', async (req, res, next) => {
  try {
    const { errors, fields } = validateTaskBody(req.body || {}, { requireTitle: true });
    if (errors.length > 0) {
      return res.status(400).json({ error: errors.join('; ') });
    }

    if (!(await ensureProject(fields.project_id))) {
      return res.status(400).json({ error: 'projectId does not reference an existing project' });
    }

    if (!fields.status) fields.status = 'prioritize';
    if (!fields.color) fields.color = await pickColor();

    const { rows } = await pool.query(
      `INSERT INTO tasks (id, title, status, start_date, color, project_id)
       VALUES (gen_random_uuid()::text, $1, $2, $3, $4, $5)
       RETURNING ${TASK_COLUMNS}`,
      [fields.title, fields.status, fields.start_date || null, fields.color, fields.project_id || null]
    );
    res.status(201).json(toTask(rows[0]));
  } catch (err) {
    next(err);
  }
});

router.get('/:id', async (req, res, next) => {
  try {
    const { rows } = await pool.query(`SELECT ${TASK_COLUMNS} FROM tasks WHERE id = $1`, [
      req.params.id,
    ]);
    if (rows.length === 0) {
      return res.status(404).json({ error: 'task not found' });
    }
    res.json(toTask(rows[0]));
  } catch (err) {
    next(err);
  }
});

router.put('/:id', async (req, res, next) => {
  try {
    const { errors, fields } = validateTaskBody(req.body || {});
    if (errors.length > 0) {
      return res.status(400).json({ error: errors.join('; ') });
    }

    const existingRes = await pool.query(
      `SELECT title, status, to_char(start_date, 'YYYY-MM-DD') AS start_date, color, project_id
       FROM tasks WHERE id = $1`,
      [req.params.id]
    );
    if (existingRes.rowCount === 0) {
      return res.status(404).json({ error: 'task not found' });
    }
    const existing = existingRes.rows[0];

    const merged = {
      title: fields.title !== undefined ? fields.title : existing.title,
      status: fields.status !== undefined ? fields.status : existing.status,
      start_date: fields.start_date !== undefined ? fields.start_date : existing.start_date,
      color: fields.color !== undefined ? fields.color : existing.color,
      project_id: fields.project_id !== undefined ? fields.project_id : existing.project_id,
    };

    if (!(await ensureProject(merged.project_id))) {
      return res.status(400).json({ error: 'projectId does not reference an existing project' });
    }

    const { rows } = await pool.query(
      `UPDATE tasks
       SET title = $2, status = $3, start_date = $4, color = $5, project_id = $6
       WHERE id = $1
       RETURNING ${TASK_COLUMNS}`,
      [req.params.id, merged.title, merged.status, merged.start_date, merged.color, merged.project_id]
    );
    res.json(toTask(rows[0]));
  } catch (err) {
    next(err);
  }
});

router.delete('/:id', async (req, res, next) => {
  try {
    const { rowCount } = await pool.query('DELETE FROM tasks WHERE id = $1', [req.params.id]);
    if (rowCount === 0) {
      return res.status(404).json({ error: 'task not found' });
    }
    res.status(204).end();
  } catch (err) {
    next(err);
  }
});

module.exports = router;
