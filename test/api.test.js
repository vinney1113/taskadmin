const { test, before, beforeEach, after } = require('node:test');
const assert = require('node:assert');
const request = require('supertest');

const pool = require('../db');
const { createApp, initDatabase } = require('../server');

const app = createApp();

before(async () => {
  await initDatabase();
});

beforeEach(async () => {
  await pool.query('TRUNCATE tasks, projects RESTART IDENTITY CASCADE');
});

after(async () => {
  await pool.end();
});

test('POST /api/tasks creates a task with default status', async () => {
  const res = await request(app).post('/api/tasks').send({ title: 'Plan sprint' });
  assert.strictEqual(res.status, 201);
  assert.strictEqual(res.body.title, 'Plan sprint');
  assert.strictEqual(res.body.status, 'prioritize');
  assert.ok(res.body.id);
  assert.ok(res.body.createdAt);
  assert.strictEqual(res.body.projectId, null);
});

test('GET /api/tasks lists tasks in creation order', async () => {
  await request(app).post('/api/tasks').send({ title: 'Plan sprint' });
  await request(app).post('/api/tasks').send({ title: 'Buy milk' });
  const res = await request(app).get('/api/tasks');
  assert.strictEqual(res.status, 200);
  assert.deepStrictEqual(
    res.body.map((t) => t.title),
    ['Plan sprint', 'Buy milk']
  );
});

test('GET /api/tasks includes permissive CORS headers', async () => {
  const res = await request(app).get('/api/tasks');
  assert.strictEqual(res.headers['access-control-allow-origin'], '*');
});

test('GET /api/tasks/:id returns a single task', async () => {
  const created = await request(app).post('/api/tasks').send({ title: 'Plan sprint' });
  const res = await request(app).get(`/api/tasks/${created.body.id}`);
  assert.strictEqual(res.status, 200);
  assert.strictEqual(res.body.title, 'Plan sprint');
});

test('GET /api/tasks/:id returns 404 for a missing task', async () => {
  const res = await request(app).get('/api/tasks/does-not-exist');
  assert.strictEqual(res.status, 404);
  assert.strictEqual(res.body.error, 'task not found');
});

test('PUT /api/tasks/:id updates title and status', async () => {
  const created = await request(app).post('/api/tasks').send({ title: 'Plan sprint' });
  const res = await request(app)
    .put(`/api/tasks/${created.body.id}`)
    .send({ title: 'Plan a sprint', status: 'in-progress' });
  assert.strictEqual(res.status, 200);
  assert.strictEqual(res.body.title, 'Plan a sprint');
  assert.strictEqual(res.body.status, 'in-progress');
});

test('DELETE /api/tasks/:id removes a task', async () => {
  const created = await request(app).post('/api/tasks').send({ title: 'Plan sprint' });
  const del = await request(app).delete(`/api/tasks/${created.body.id}`);
  assert.strictEqual(del.status, 204);
  const res = await request(app).get(`/api/tasks/${created.body.id}`);
  assert.strictEqual(res.status, 404);
});

test('POST /api/tasks rejects an empty title', async () => {
  const res = await request(app).post('/api/tasks').send({ title: '   ' });
  assert.strictEqual(res.status, 400);
});

test('POST /api/tasks rejects an invalid status', async () => {
  const res = await request(app)
    .post('/api/tasks')
    .send({ title: 'Plan sprint', status: 'nonsense' });
  assert.strictEqual(res.status, 400);
});

test('POST /api/tasks rejects an unknown projectId', async () => {
  const res = await request(app)
    .post('/api/tasks')
    .send({ title: 'Plan sprint', projectId: 'does-not-exist' });
  assert.strictEqual(res.status, 400);
});

test('POST /api/tasks rejects an unsafe color value', async () => {
  const res = await request(app)
    .post('/api/tasks')
    .send({ title: 'Plan sprint', color: 'dark" onmouseover="alert(1)' });
  assert.strictEqual(res.status, 400);
});

test('PUT /api/tasks rejects an unsafe color value', async () => {
  const created = await request(app).post('/api/tasks').send({ title: 'Plan sprint' });
  const res = await request(app)
    .put(`/api/tasks/${created.body.id}`)
    .send({ color: 'x" onclick="evil()' });
  assert.strictEqual(res.status, 400);
});

test('PUT /api/tasks/:id returns 404 for a missing task', async () => {
  const res = await request(app).put('/api/tasks/does-not-exist').send({ title: 'Nope' });
  assert.strictEqual(res.status, 404);
});

test('POST /api/projects creates a project', async () => {
  const res = await request(app).post('/api/projects').send({ name: 'Office Project' });
  assert.strictEqual(res.status, 201);
  assert.strictEqual(res.body.name, 'Office Project');
  assert.strictEqual(res.body.icon, 'default');
});

test('POST /api/projects rejects a duplicate name', async () => {
  await request(app).post('/api/projects').send({ name: 'Office Project' });
  const res = await request(app).post('/api/projects').send({ name: 'Office Project' });
  assert.strictEqual(res.status, 409);
});

test('DELETE /api/projects/:id unlinks its tasks', async () => {
  const project = await request(app).post('/api/projects').send({ name: 'Office Project' });
  const task = await request(app)
    .post('/api/tasks')
    .send({ title: 'Plan sprint', projectId: project.body.id });
  const del = await request(app).delete(`/api/projects/${project.body.id}`);
  assert.strictEqual(del.status, 204);
  const res = await request(app).get(`/api/tasks/${task.body.id}`);
  assert.strictEqual(res.body.projectId, null);
});
