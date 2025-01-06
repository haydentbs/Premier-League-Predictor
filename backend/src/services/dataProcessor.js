const { Pool } = require('pg');
const config = require('../config/database');

class DataProcessor {
    constructor() {
        this.pool = new Pool(config);
    }

    async processNewMatch(matchData) {
        const client = await this.pool.connect();
        try {
            await client.query('BEGIN');

            // Insert match data
            const matchResult = await client.query(
                `INSERT INTO matches (
                    home_team_id, away_team_id, home_score, away_score, 
                    match_date, season, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7) 
                RETURNING match_id`,
                [
                    matchData.homeTeamId,
                    matchData.awayTeamId,
                    matchData.homeScore,
                    matchData.awayScore,
                    matchData.date,
                    matchData.season,
                    matchData.status
                ]
            );

            // Calculate and insert match features
            if (matchData.status === 'FINISHED') {
                await this.calculateAndInsertFeatures(client, matchResult.rows[0].match_id);
            }

            await client.query('COMMIT');
            return matchResult.rows[0];
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    async calculateAndInsertFeatures(client, matchId) {
        // Get match details
        const match = await client.query(
            'SELECT * FROM matches WHERE match_id = $1',
            [matchId]
        );

        // Get team statistics
        const homeStats = await client.query(
            'SELECT * FROM team_stats WHERE team_id = $1',
            [match.rows[0].home_team_id]
        );

        const awayStats = await client.query(
            'SELECT * FROM team_stats WHERE team_id = $1',
            [match.rows[0].away_team_id]
        );

        // Calculate features
        const features = {
            home_team_form: this.calculateForm(homeStats.rows[0]),
            away_team_form: this.calculateForm(awayStats.rows[0]),
            home_team_win_rate: homeStats.rows[0].wins / homeStats.rows[0].matches_played,
            away_team_win_rate: awayStats.rows[0].wins / awayStats.rows[0].matches_played,
            // Add more feature calculations as needed
        };

        // Insert features
        await client.query(
            `INSERT INTO match_features (
                match_id, home_team_form, away_team_form,
                home_team_win_rate, away_team_win_rate
            ) VALUES ($1, $2, $3, $4, $5)`,
            [
                matchId,
                features.home_team_form,
                features.away_team_form,
                features.home_team_win_rate,
                features.away_team_win_rate
            ]
        );
    }

    calculateForm(teamStats) {
        // Simple form calculation (can be enhanced)
        return (teamStats.wins * 3 + teamStats.draws) / (teamStats.matches_played * 3);
    }
}

module.exports = new DataProcessor();