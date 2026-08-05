const fs = require('fs');
const path = require('path');
const express = require('express');
const pool = require('./db');
const tasksRouter = require('./routes/tasks');
const projectsRouter = require('./routes/projects');

const DEFAULT_PROJECTS = [
  { name: 'Office Project', icon: 'briefcase' },
  { name: 'Personal Project', icon: 'user' },
  { name: 'Daily Study', icon: 'book' },
];

const SCHEMA_PATH = path.join(__dirname, 'schema.sql');

async function applySchema() {
  const sql = fs.readFileSync(SCHEMA_PATH, 'utf8');
  await pool.query(sql);
}

async function seedDefaultProjects() {
  const { rowCount } = await pool.query('SELECT 1 FROM projects LIMIT 1');
  if (rowCount > 0) return;
  for (const project of DEFAULT_PROJECTS) {
    await pool.query(
      `INSERT INTO projects (id, name, icon)
       VALUES (gen_random_uuid()::text, $1, $2)`,
      [project.name, project.icon]
    );
  }
}

async function initDatabase() {
  await applySchema();
  await seedDefaultProjects();
}

function createApp() {
  const app = express();
  app.use(express.json());

  app.use('/api/tasks', tasksRouter);
  app.use('/api/projects', projectsRouter);

  app.use('/vendor', express.static(path.join(__dirname, 'vendor')));
  app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'index.html')));
  app.get('/index.html', (req, res) => res.sendFile(path.join(__dirname, 'index.html')));
  app.get('/styles.css', (req, res) => res.sendFile(path.join(__dirname, 'styles.css')));
  app.get('/app.js', (req, res) => res.sendFile(path.join(__dirname, 'app.js')));

  app.use((req, res) => {
    res.status(404).json({ error: 'not found' });
  });

  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
      return res.status(400).json({ error: 'invalid JSON body' });
    }
    console.error(err);
    res.status(500).json({ error: 'internal server error' });
  });

  return app;
}

async function start() {
  await initDatabase();
  const port = Number(process.env.PORT) || 3000;
  const server = createApp().listen(port, () => {
    console.log(`taskadmin API listening on http://127.0.0.1:${port}`);
  });
  return server;
}

if (require.main === module) {
  start().catch((err) => {
    console.error('failed to start server:', err);
    process.exit(1);
  });
}

module.exports = { createApp, initDatabase, start };
