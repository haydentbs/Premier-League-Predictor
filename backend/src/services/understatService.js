const { Understat } = require('understat');
const pool = require('../config/database');

class UnderstatService {
    constructor() {
        this.understat = new Understat();
        // Define seasons we want to track
        this.seasons = ['2023', '2022', '2021'];  // Can add more past seasons
    }

    async updateAllData() {
        try {
            console.log('Starting data update...');
            await this.updateFixtures();  // Get upcoming matches
            
            // Update results for all tracked seasons
            for (const season of this.seasons) {
                await this.updateResults(season);
            }
            
            console.log('Data update completed');
        } catch (error) {
            console.error('Error in updateAllData:', error);
            throw error;
        }
    }

    async updateFixtures() {
        try {
            console.log('Fetching upcoming fixtures...');
            // Get fixtures for EPL (only gets current season fixtures)
            const fixtures = await this.understat.league.getFixtures('epl');
            
            const client = await pool.connect();
            try {
                await client.query('BEGIN');

                for (const fixture of fixtures) {
                    const homeTeamId = await this.ensureTeamExists(client, fixture.h.team_name);
                    const awayTeamId = await this.ensureTeamExists(client, fixture.a.team_name);

                    await client.query(`
                        INSERT INTO matches (
                            home_team_id, away_team_id,
                            match_date,
                            season,
                            status
                        )
                        VALUES ($1, $2, $3, $4, 'SCHEDULED')
                        ON CONFLICT (match_date, home_team_id, away_team_id)
                        DO NOTHING
                    `, [
                        homeTeamId,
                        awayTeamId,
                        new Date(fixture.datetime),
                        fixture.season
                    ]);
                }

                await client.query('COMMIT');
                console.log('Fixtures updated successfully');
            } catch (error) {
                await client.query('ROLLBACK');
                throw error;
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Error updating fixtures:', error);
            throw error;
        }
    }

    async updateResults(season) {
        try {
            console.log(`Fetching results for season ${season}...`);
            const results = await this.understat.league.getResults('epl', season);
            
            const client = await pool.connect();
            try {
                await client.query('BEGIN');

                for (const match of results) {
                    const homeTeamId = await this.ensureTeamExists(client, match.h.team_name);
                    const awayTeamId = await this.ensureTeamExists(client, match.a.team_name);

                    await client.query(`
                        INSERT INTO matches (
                            home_team_id, away_team_id,
                            home_score, away_score,
                            match_date,
                            season,
                            status,
                            home_xg, away_xg
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, 'FINISHED', $7, $8)
                        ON CONFLICT (match_date, home_team_id, away_team_id)
                        DO UPDATE SET
                            home_score = EXCLUDED.home_score,
                            away_score = EXCLUDED.away_score,
                            status = 'FINISHED',
                            home_xg = EXCLUDED.home_xg,
                            away_xg = EXCLUDED.away_xg
                        WHERE matches.status != 'FINISHED'
                    `, [
                        homeTeamId,
                        awayTeamId,
                        match.goals.h,
                        match.goals.a,
                        new Date(match.datetime),
                        season,
                        match.xG.h,
                        match.xG.a
                    ]);
                }

                await client.query('COMMIT');
                console.log(`Results updated successfully for season ${season}`);
            } catch (error) {
                await client.query('ROLLBACK');
                throw error;
            } finally {
                client.release();
            }
        } catch (error) {
            console.error(`Error updating results for season ${season}:`, error);
            throw error;
        }
    }

    async ensureTeamExists(client, teamName) {
        const result = await client.query(
            'INSERT INTO teams (team_name) VALUES ($1) ON CONFLICT (team_name) DO UPDATE SET team_name = $1 RETURNING team_id',
            [teamName]
        );
        return result.rows[0].team_id;
    }

    // Utility method to get match statistics
    async getMatchStats() {
        const stats = await pool.query(`
            SELECT 
                COUNT(*) as total_matches,
                COUNT(*) FILTER (WHERE status = 'FINISHED') as completed_matches,
                COUNT(*) FILTER (WHERE status = 'SCHEDULED') as upcoming_matches,
                MAX(match_date) FILTER (WHERE status = 'FINISHED') as latest_result,
                MIN(match_date) FILTER (WHERE status = 'SCHEDULED') as next_fixture
            FROM matches
        `);
        return stats.rows[0];
    }
}

module.exports = new UnderstatService();