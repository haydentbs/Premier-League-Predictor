const { Pool } = require('pg');

// Create a new pool instance
const pool = new Pool({
    host: process.env.POSTGRES_HOST || 'db',
    port: process.env.POSTGRES_PORT || 5432,
    database: process.env.POSTGRES_DB || 'premier_league',
    user: process.env.POSTGRES_USER || 'postgres',
    password: process.env.POSTGRES_PASSWORD || 'postgres',
});

// Test the connection
pool.on('error', (err) => {
    console.error('Unexpected error on idle client', err);
});

module.exports = pool;