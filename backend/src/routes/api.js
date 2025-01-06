const express = require('express');
const router = express.Router();
const pool = require('../config/database');
const understatService = require('../services/understatService');

// Basic API test endpoint
router.get('/test', (req, res) => {
    res.json({
        message: 'API is working!',
        timestamp: new Date().toISOString()
    });
});

// Database test endpoint
router.get('/db-test', async (req, res) => {
    try {
        const result = await pool.query('SELECT NOW()');
        res.json({
            message: 'Database connected!',
            timestamp: result.rows[0].now
        });
    } catch (error) {
        res.status(500).json({
            message: 'Database connection failed',
            error: error.message
        });
    }
});

router.post('/query', async (req, res) => {
    try {
        const { query } = req.body;
        
        // Basic security check - only allow SELECT queries
        if (!query.trim().toLowerCase().startsWith('select')) {
            return res.status(400).json({
                message: 'Only SELECT queries are allowed',
                error: 'Invalid query type'
            });
        }

        const result = await pool.query(query);
        res.json({
            message: 'Query executed successfully',
            data: result.rows,
            rowCount: result.rowCount
        });
    } catch (error) {
        res.status(500).json({
            message: 'Query execution failed',
            error: error.message
        });
    }
});



router.get('/teams', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM teams ORDER BY team_name');
        res.json({
            message: 'Teams retrieved successfully',
            data: result.rows
        });
    } catch (error) {
        res.status(500).json({
            message: 'Failed to retrieve teams',
            error: error.message
        });
    }
});

// Get all matches with team names
router.get('/matches', async (req, res) => {
    try {
        const result = await pool.query(`
            SELECT 
                m.match_id,
                ht.team_name as home_team,
                at.team_name as away_team,
                m.home_score,
                m.away_score,
                m.match_date,
                m.season,
                m.status
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.team_id
            JOIN teams at ON m.away_team_id = at.team_id
            ORDER BY m.match_date DESC
        `);
        res.json({
            message: 'Matches retrieved successfully',
            data: result.rows
        });
    } catch (error) {
        res.status(500).json({
            message: 'Failed to retrieve matches',
            error: error.message
        });
    }
});

// Get matches for a specific team
router.get('/teams/:teamId/matches', async (req, res) => {
    try {
        const { teamId } = req.params;
        const result = await pool.query(`
            SELECT 
                m.match_id,
                ht.team_name as home_team,
                at.team_name as away_team,
                m.home_score,
                m.away_score,
                m.match_date,
                m.status
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.team_id
            JOIN teams at ON m.away_team_id = at.team_id
            WHERE m.home_team_id = $1 OR m.away_team_id = $1
            ORDER BY m.match_date DESC
        `, [teamId]);
        res.json({
            message: 'Team matches retrieved successfully',
            data: result.rows
        });
    } catch (error) {
        res.status(500).json({
            message: 'Failed to retrieve team matches',
            error: error.message
        });
    }
});

// Manually trigger data update
router.post('/update-data', async (req, res) => {
    try {
        const { season = '2023' } = req.body;
        await understatService.fetchAndStoreSeason(season);
        res.json({
            message: 'Data update triggered successfully'
        });
    } catch (error) {
        res.status(500).json({
            message: 'Failed to update data',
            error: error.message
        });
    }
});

module.exports = router;