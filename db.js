const { Pool } = require('pg');

const DATABASE_URL =
  process.env.DATABASE_URL || 'postgres://postgres@127.0.0.1:5432/taskadmin';

// Render Postgres requires TLS for every connection. The internal
// connection string injected via fromDatabase carries no sslmode, so
// enable SSL for any non-local host. Local dev uses trust auth over
// 127.0.0.1, which must keep TLS off.
const isLocalHost = /localhost|127\.0\.0\.1/.test(DATABASE_URL);

const pool = new Pool({
  connectionString: DATABASE_URL,
  ssl: isLocalHost ? undefined : { rejectUnauthorized: false },
});

module.exports = pool;
