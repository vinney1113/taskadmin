const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgres://postgres@127.0.0.1:5432/taskadmin',
});

module.exports = pool;
