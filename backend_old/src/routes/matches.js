const express = require('express');
const router = express.Router();
const pool = require('../config/database');

// Get matches with features
router.get('/matches/with-features', async (req, res) => {
    try {
        const result = await pool.query(`
            SELECT 
                m.*,
                mf.*,
                ht.team_name as home_team,
                at.team_name as away_team,
                hts.form_points as home_team_form,
                ats.form_points as away_team_form
            FROM matches m
            JOIN match_features mf ON m.match_id = mf.match_id
            JOIN teams ht ON m.home_team_id = ht.team_id
            JOIN teams at ON m.away_team_id = at.team_id
            JOIN team_stats hts ON m.home_team_id = hts.team_id
            JOIN team_stats ats ON m.away_team_id = ats.team_id
            ORDER BY m.match_date DESC
        `);
        res.json(result.rows);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;