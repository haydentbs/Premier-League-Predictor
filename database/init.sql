-- Teams table for storing team information
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches table for raw match data
CREATE TABLE matches (
    match_id SERIAL PRIMARY KEY,
    home_team_id INTEGER REFERENCES teams(team_id),
    away_team_id INTEGER REFERENCES teams(team_id),
    home_score INTEGER,
    away_score INTEGER,
    match_date TIMESTAMP,
    season VARCHAR(10),
    status VARCHAR(20), -- 'SCHEDULED', 'FINISHED', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Team Statistics table for computed features
CREATE TABLE team_stats (
    stat_id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(team_id),
    season VARCHAR(10),
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    goals_scored INTEGER DEFAULT 0,
    goals_conceded INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0,
    form_points INTEGER DEFAULT 0, -- Last 5 games
    home_wins INTEGER DEFAULT 0,
    away_wins INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Match Features table for ML inputs
CREATE TABLE match_features (
    feature_id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(match_id),
    home_team_form FLOAT,
    away_team_form FLOAT,
    home_team_goals_scored_avg FLOAT,
    home_team_goals_conceded_avg FLOAT,
    away_team_goals_scored_avg FLOAT,
    away_team_goals_conceded_avg FLOAT,
    home_team_win_rate FLOAT,
    away_team_win_rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert Mock Data
-- -- Premier League Teams
-- INSERT INTO teams (team_name) VALUES
--     ('Arsenal'),
--     ('Aston Villa'),
--     ('Chelsea'),
--     ('Liverpool'),
--     ('Manchester City'),
--     ('Manchester United'),
--     ('Newcastle United'),
--     ('Tottenham Hotspur');

-- -- Mock Matches
-- INSERT INTO matches (home_team_id, away_team_id, home_score, away_score, match_date, season, status) VALUES
--     (1, 2, 3, 1, '2024-03-01 15:00:00', '2023/24', 'FINISHED'),
--     (3, 4, 1, 2, '2024-03-02 17:30:00', '2023/24', 'FINISHED'),
--     (5, 6, 3, 3, '2024-03-03 14:00:00', '2023/24', 'FINISHED'),
--     (7, 8, 0, 2, '2024-03-04 20:00:00', '2023/24', 'FINISHED'),
--     (2, 3, 1, 1, '2024-03-09 15:00:00', '2023/24', 'FINISHED'),
--     (4, 1, null, null, '2024-03-16 15:00:00', '2023/24', 'SCHEDULED'),
--     (6, 8, null, null, '2024-03-17 16:30:00', '2023/24', 'SCHEDULED');

-- Create functions to automatically update statistics
CREATE OR REPLACE FUNCTION update_team_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update home team stats
    UPDATE team_stats
    SET 
        matches_played = matches_played + 1,
        goals_scored = goals_scored + NEW.home_score,
        goals_conceded = goals_conceded + NEW.away_score,
        wins = CASE WHEN NEW.home_score > NEW.away_score THEN wins + 1 ELSE wins END,
        draws = CASE WHEN NEW.home_score = NEW.away_score THEN draws + 1 ELSE draws END,
        losses = CASE WHEN NEW.home_score < NEW.away_score THEN losses + 1 ELSE losses END,
        clean_sheets = CASE WHEN NEW.away_score = 0 THEN clean_sheets + 1 ELSE clean_sheets END,
        home_wins = CASE WHEN NEW.home_score > NEW.away_score THEN home_wins + 1 ELSE home_wins END,
        last_updated = CURRENT_TIMESTAMP
    WHERE team_id = NEW.home_team_id AND season = NEW.season;

    -- Update away team stats
    UPDATE team_stats
    SET 
        matches_played = matches_played + 1,
        goals_scored = goals_scored + NEW.away_score,
        goals_conceded = goals_conceded + NEW.home_score,
        wins = CASE WHEN NEW.away_score > NEW.home_score THEN wins + 1 ELSE wins END,
        draws = CASE WHEN NEW.home_score = NEW.away_score THEN draws + 1 ELSE draws END,
        losses = CASE WHEN NEW.away_score < NEW.home_score THEN losses + 1 ELSE losses END,
        clean_sheets = CASE WHEN NEW.home_score = 0 THEN clean_sheets + 1 ELSE clean_sheets END,
        away_wins = CASE WHEN NEW.away_score > NEW.home_score THEN away_wins + 1 ELSE away_wins END,
        last_updated = CURRENT_TIMESTAMP
    WHERE team_id = NEW.away_team_id AND season = NEW.season;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic stats updates
CREATE TRIGGER match_stats_update
AFTER INSERT OR UPDATE ON matches
FOR EACH ROW
WHEN (NEW.status = 'FINISHED')
EXECUTE FUNCTION update_team_stats();

ALTER TABLE matches ADD COLUMN IF NOT EXISTS home_xg FLOAT;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS away_xg FLOAT;

-- Add unique constraint to prevent duplicate matches
ALTER TABLE matches ADD CONSTRAINT unique_match 
    UNIQUE (match_date, home_team_id, away_team_id);