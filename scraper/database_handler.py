from sqlalchemy import create_engine, text
from datetime import datetime
import time
import pandas as pd

class DatabaseHandler:
    def __init__(self, db_config, df):
        self.db_config = db_config
        self.df = df
        self.engine = self.create_connection()

    def create_connection(self):
        # Create PostgreSQL connection URL
        db_url = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        return create_engine(db_url)

    def insert_data(self):
        try:
            # Insert DataFrame to matches table
            self.df.to_sql(
                'matches', 
                self.engine, 
                if_exists='append',  # 'append' will add new records, 'replace' would overwrite the table
                index=False,
                method='multi'
            )
            print(f"Successfully inserted {len(self.df)} rows into matches table")
            return True
        except Exception as e:
            print(f"Error inserting data: {str(e)}")
            return False
        
    def insert_teams(self):
        try:
            # Get unique teams from both Team and Opponent columns
            # teams = pd.concat([
            #     self.df['Team'].unique(),
            #     self.df['Opponent'].unique()
            # ]).unique()

            teams = self.df['Team'].unique()
            
            # Create DataFrame of teams
            teams_df = pd.DataFrame({'team_name': teams})
            
            # Insert teams with ON CONFLICT DO NOTHING to handle existing teams
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO teams (team_name)
                    SELECT unnest(:teams)
                    ON CONFLICT (team_name) DO NOTHING
                """), {'teams': list(teams)})
                conn.commit()
            
            print(f"Successfully processed {len(teams)} teams")
            return True
        except Exception as e:
            print(f"Error inserting teams: {str(e)}")
            return False

    def get_team_ids(self):
        try:
            # Get team ID mappings
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT team_id, team_name FROM teams"))
                team_mapping = {row.team_name: row.team_id for row in result}
            
            # Add team_id and opponent_id columns
            self.df['team_id'] = self.df['Team'].map(team_mapping)
            self.df['opponent_id'] = self.df['Opponent'].map(team_mapping)
            
            return True
        except Exception as e:
            print(f"Error getting team IDs: {str(e)}")
            return False

    def insert_data_safe(self):
        try:
            # First, insert teams and get their IDs
            self.insert_teams()
            self.get_team_ids()
            
            # Create temporary table
            temp_table_name = 'temp_matches'
            temp_df = self.df.copy()
            
            # Replace empty strings or other null-like values with None/NULL
            temp_df = temp_df.replace(['', 'None', 'NULL'], None)
            # Convert numeric columns to float to handle NaN properly
            numeric_columns = ['xg', 'xga', 'goals', 'opponent_goals', 
                             'rolling_xg', 'rolling_xga', 'rolling_xg_diff', 
                             'rolling_xga_diff', 'form_rolling_5', 'form_rolling_10',
                             'opponent_form_rolling_3', 'opponent_form_rolling_6']
            temp_df[numeric_columns] = temp_df[numeric_columns].astype(float)
            
            # Insert into temporary table
            temp_df.to_sql(
                temp_table_name,
                self.engine,
                if_exists='replace',
                index=False
            )

            # Insert from temp table to main table
            with self.engine.connect() as conn:
                conn.execute(text(f"""
                    INSERT INTO matches (
                        date_of_match, team_id, opponent_id,
                        xg, xga, goals, opponent_goals,
                        status_of_match, result, location_of_match,
                        rolling_xg, rolling_xga,
                        rolling_xg_diff, rolling_xga_diff,
                        form_rolling_5, form_rolling_10,
                        opponent_form_rolling_3, opponent_form_rolling_6
                    )
                    SELECT 
                        "Date"::timestamp, team_id, opponent_id,
                        NULLIF(xg, 'NaN')::float,
                        NULLIF(xga, 'NaN')::float,
                        NULLIF(goals, 'NaN')::integer,
                        NULLIF(opponent_goals, 'NaN')::integer,
                        NULLIF("Status", '')::varchar,
                        NULLIF("Result", 'NaN')::integer,
                        NULLIF(location, '')::varchar,
                        NULLIF(rolling_xg, 'NaN')::float,
                        NULLIF(rolling_xga, 'NaN')::float,
                        NULLIF(rolling_xg_diff, 'NaN')::float,
                        NULLIF(rolling_xga_diff, 'NaN')::float,
                        NULLIF(form_rolling_5, 'NaN')::float,
                        NULLIF(form_rolling_10, 'NaN')::float,
                        NULLIF(opponent_form_rolling_3, 'NaN')::float,
                        NULLIF(opponent_form_rolling_6, 'NaN')::float
                    FROM {temp_table_name}
                    ON CONFLICT (date_of_match, team_id, opponent_id)
                    DO UPDATE SET
                        xg = EXCLUDED.xg,
                        xga = EXCLUDED.xga,
                        goals = EXCLUDED.goals,
                        opponent_goals = EXCLUDED.opponent_goals,
                        status_of_match = EXCLUDED.status_of_match,
                        result = EXCLUDED.result,
                        rolling_xg = EXCLUDED.rolling_xg,
                        rolling_xga = EXCLUDED.rolling_xga,
                        rolling_xg_diff = EXCLUDED.rolling_xg_diff,
                        rolling_xga_diff = EXCLUDED.rolling_xga_diff,
                        form_rolling_5 = EXCLUDED.form_rolling_5,
                        form_rolling_10 = EXCLUDED.form_rolling_10,
                        opponent_form_rolling_3 = EXCLUDED.opponent_form_rolling_3,
                        opponent_form_rolling_6 = EXCLUDED.opponent_form_rolling_6
                """))
                conn.commit()

            # Drop temporary table
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))
                conn.commit()

            print(f"Successfully inserted/updated {len(self.df)} rows in matches table")
            return True
        except Exception as e:
            print(f"Error inserting data: {str(e)}")
            return False