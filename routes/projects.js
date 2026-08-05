const express = require('express');
const pool = require('../db');

const router = express.Router();

function isDateString(value) {
  return (
    typeof value === 'string' &&
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(new Date(`${value}T00:00:00`).getTime())
  );
}

function toProject(row) {
  return {
    id: row.id,
    name: row.name,
    icon: row.icon,
    startDate: row.start_date || null,
    endDate: row.end_date || null,
    description: row.description || '',
    createdAt: new Date(row.created_at).toISOString(),
  };
}

const PROJECT_COLUMNS = `
  id, name, icon, description, created_at,
  to_char(start_date, 'YYYY-MM-DD') AS start_date,
  to_char(end_date, 'YYYY-MM-DD') AS end_date
`;

function validateProjectBody(body, { requireName = false } = {}) {
  const errors = [];
  const fields = {};

  if (requireName || body.name !== undefined) {
    if (typeof body.name !== 'string' || !body.name.trim()) {
      errors.push('name is required and must not be empty');
    } else if (body.name.trim().length > 255) {
      errors.push('name must be 255 characters or fewer');
    } else {
      fields.name = body.name.trim();
    }
  }

  if (body.icon !== undefined) {
    fields.icon = body.icon;
  }

  if (body.description !== undefined) {
    fields.description = body.description;
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

  if (body.endDate !== undefined) {
    if (body.endDate === null) {
      fields.end_date = null;
    } else if (!isDateString(body.endDate)) {
      errors.push('endDate must be a valid YYYY-MM-DD date');
    } else {
      fields.end_date = body.endDate;
    }
  }

  if (
    fields.start_date &&
    fields.end_date &&
    fields.end_date < fields.start_date
  ) {
    errors.push('endDate cannot be before startDate');
  }

  return { errors, fields };
}

function isUniqueViolation(err) {
  return err.code === '23505';
}

router.get('/', async (req, res, next) => {
  try {
    const { rows } = await pool.query(
      `SELECT ${PROJECT_COLUMNS} FROM projects ORDER BY created_at, id`
    );
    res.json(rows.map(toProject));
  } catch (err) {
    next(err);
  }
});

router.post('/', async (req, res, next) => {
  try {
    const { errors, fields } = validateProjectBody(req.body || {}, { requireName: true });
    if (errors.length > 0) {
      return res.status(400).json({ error: errors.join('; ') });
    }

    if (!fields.icon) fields.icon = 'default';
    if (!fields.description) fields.description = '';

    const { rows } = await pool.query(
      `INSERT INTO projects (id, name, icon, start_date, end_date, description)
       VALUES (gen_random_uuid()::text, $1, $2, $3, $4, $5)
       RETURNING ${PROJECT_COLUMNS}`,
      [fields.name, fields.icon, fields.start_date || null, fields.end_date || null, fields.description]
    );
    res.status(201).json(toProject(rows[0]));
  } catch (err) {
    if (isUniqueViolation(err)) {
      return res.status(409).json({ error: 'a project with that name already exists' });
    }
    next(err);
  }
});

router.get('/:id', async (req, res, next) => {
  try {
    const { rows } = await pool.query(
      `SELECT ${PROJECT_COLUMNS} FROM projects WHERE id = $1`,
      [req.params.id]
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: 'project not found' });
    }
    res.json(toProject(rows[0]));
  } catch (err) {
    next(err);
  }
});

router.put('/:id', async (req, res, next) => {
  try {
    const { errors, fields } = validateProjectBody(req.body || {});
    if (errors.length > 0) {
      return res.status(400).json({ error: errors.join('; ') });
    }

    const existingRes = await pool.query(
      `SELECT name, icon, description,
              to_char(start_date, 'YYYY-MM-DD') AS start_date,
              to_char(end_date, 'YYYY-MM-DD') AS end_date
       FROM projects WHERE id = $1`,
      [req.params.id]
    );
    if (existingRes.rowCount === 0) {
      return res.status(404).json({ error: 'project not found' });
    }
    const existing = existingRes.rows[0];

    const merged = {
      name: fields.name !== undefined ? fields.name : existing.name,
      icon: fields.icon !== undefined ? fields.icon : existing.icon,
      description: fields.description !== undefined ? fields.description : existing.description,
      start_date: fields.start_date !== undefined ? fields.start_date : existing.start_date,
      end_date: fields.end_date !== undefined ? fields.end_date : existing.end_date,
    };

    const { rows } = await pool.query(
      `UPDATE projects
       SET name = $2, icon = $3, start_date = $4, end_date = $5, description = $6
       WHERE id = $1
       RETURNING ${PROJECT_COLUMNS}`,
      [
        req.params.id,
        merged.name,
        merged.icon,
        merged.start_date,
        merged.end_date,
        merged.description,
      ]
    );
    res.json(toProject(rows[0]));
  } catch (err) {
    if (isUniqueViolation(err)) {
      return res.status(409).json({ error: 'a project with that name already exists' });
    }
    next(err);
  }
});

router.delete('/:id', async (req, res, next) => {
  try {
    const { rowCount } = await pool.query('DELETE FROM projects WHERE id = $1', [req.params.id]);
    if (rowCount === 0) {
      return res.status(404).json({ error: 'project not found' });
    }
    res.status(204).end();
  } catch (err) {
    next(err);
  }
});

module.exports = router;
