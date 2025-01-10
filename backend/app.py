from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
import pandas as pd

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],  # Your frontend URL
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Database configuration
db_config = {
    'user': 'postgres',
    'password': 'postgres',
    'host': 'db',  # This matches the service name in docker-compose
    'port': '5432',
    'database': 'premier_league'
}

# Create database connection
db_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
engine = create_engine(db_url)

@app.route('/teams', methods=['GET'])
def get_teams():
    try:
        query = "SELECT * FROM teams"
        df = pd.read_sql(query, engine)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/matches', methods=['GET'])
def get_matches():
    try:
        # Get query parameters
        limit = request.args.get('limit', 3000, type=int)
        team = request.args.get('team')
        
        query = """
            SELECT 
                m.date_of_match,
                ht.team_name as team,
                at.team_name as opponent,
                m.goals,
                m.opponent_goals,
                m.xg,
                m.xga,
                m.status_of_match,
                m.result,
                m.location_of_match,
                m.rolling_xg,
                m.rolling_xga,
                m.rolling_xg_diff,
                m.rolling_xga_diff,
                m.form_rolling_5,
                m.form_rolling_10,
                m.opponent_form_rolling_3,
                m.opponent_form_rolling_6
            FROM matches m
            JOIN teams ht ON m.team_id = ht.team_id
            JOIN teams at ON m.opponent_id = at.team_id
        """
        
        if team:
            query += f" WHERE ht.team_name = '{team}'"
            
        query += " ORDER BY m.date_of_match DESC LIMIT :limit"
        
        df = pd.read_sql(text(query), engine, params={'limit': limit})
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/team_stats', methods=['GET'])
def get_team_stats():
    try:
        team = request.args.get('team')
        if not team:
            return jsonify({'error': 'Team parameter is required'}), 400

        query = """
            SELECT 
                t.team_name,
                COUNT(*) as matches_played,
                AVG(m.goals) as avg_goals_scored,
                AVG(m.opponent_goals) as avg_goals_conceded,
                AVG(m.xg) as avg_xg,
                AVG(m.xga) as avg_xga,
                AVG(m.form_rolling_5) as recent_form
            FROM matches m
            JOIN teams t ON m.team_id = t.team_id
            WHERE t.team_name = :team
            GROUP BY t.team_name
        """
        
        df = pd.read_sql(text(query), engine, params={'team': team})
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)