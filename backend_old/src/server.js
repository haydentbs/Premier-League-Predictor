const express = require('express');
const cors = require('cors');
const apiRoutes = require('./routes/api');
const pool = require('./config/database');

const app = express();
const port = process.env.PORT || 5001;

// Configure CORS
app.use(cors({
    origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true
}));

app.use(express.json());

// Enhanced health check endpoint
app.get('/health', async (req, res) => {
    try {
        // Test database connection
        const dbResult = await pool.query('SELECT NOW()');
        res.json({
            status: 'ok',
            timestamp: new Date().toISOString(),
            database: 'connected',
            dbTimestamp: dbResult.rows[0].now
        });
    } catch (error) {
        console.error('Health check failed:', error);
        res.status(500).json({
            status: 'error',
            timestamp: new Date().toISOString(),
            error: error.message,
            database: 'disconnected'
        });
    }
});

// Mount API routes
app.use('/api', apiRoutes);

// Start server with detailed logging
const server = app.listen(port, '0.0.0.0', () => {
    console.log('=================================');
    console.log(`Server Configuration:`);
    console.log(`Port: ${port}`);
    console.log(`Database Host: ${process.env.POSTGRES_HOST}`);
    console.log(`Database Port: ${process.env.POSTGRES_PORT}`);
    console.log(`Database Name: ${process.env.POSTGRES_DB}`);
    console.log(`Database User: ${process.env.POSTGRES_USER}`);
    console.log('=================================');
});

// Handle server errors
server.on('error', (error) => {
    console.error('Server error:', error);
});

// Handle process termination
process.on('SIGTERM', () => {
    console.log('SIGTERM received. Shutting down gracefully...');
    server.close(() => {
        console.log('Server closed');
        pool.end();
        process.exit(0);
    });
});