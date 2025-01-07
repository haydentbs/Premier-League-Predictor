const express = require('express');
const router = express.Router();
const pool = require('../config/database');

// Basic API test endpoint
router.get('/test', (req, res) => {
    res.json({
        message: 'API is working!',
        timestamp: new Date().toISOString()
    });
});

// Get all matches
router.get('/matches', async (req, res) => {
    console.log('Fetching matches from database...');
    try {
        const result = await pool.query(`
            SELECT 
                m.match_id,
                ht.team_name as home_team,
                at.team_name as away_team,
                m.home_score,
                m.away_score,
                m.home_xg,
                m.away_xg,
                m.match_date,
                m.season,
                m.status,
                m.rolling_xg,
                m.rolling_xga,
                m.form_5,
                m.form_10
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.team_id
            JOIN teams at ON m.away_team_id = at.team_id
            ORDER BY m.match_date DESC
        `);
        
        console.log(`Successfully retrieved ${result.rows.length} matches`);
        res.json({
            message: 'Matches retrieved successfully',
            data: result.rows
        });
    } catch (error) {
        console.error('Error fetching matches:', error);
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

// Get all teams
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