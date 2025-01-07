import os
import time
from datetime import datetime
import schedule
import pandas as pd
from io import StringIO 
import psycopg2
from sqlalchemy import create_engine, String, Integer, Float, DateTime, text
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sys
from bs4 import BeautifulSoup

class Scraper:
    def __init__(self, seasons):
        self.base_url = 'https://fbref.com/en/comps/9/'
        self.seasons = seasons

        # Configure Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')  # Run in headless mode
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        
        # Add random user agent
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.chrome_options.add_argument(f'user-agent={user_agent}')
        
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'db'),
            'database': os.getenv('POSTGRES_DB', 'premier_league'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }

    def get_url(self, season):
        return f'{self.base_url}20{season}-20{season+1}/schedule/20{season}-20{season+1}-Premier-League-Scores-and-Fixtures'

    def scrape_website(self, season):
        try:
            print(f"Scraping season {season}...")
            driver = webdriver.Chrome(options=self.chrome_options)
            
            try:
                url = self.get_url(season)
                print(f"Accessing URL: {url}")
                driver.get(url)
                
                # Wait for tables to load
                print("Waiting for page to load...")
                time.sleep(5)  # Allow JavaScript to render
                
                # Find all tables
                tables = driver.find_elements(By.TAG_NAME, "table")
                print(f"Found {len(tables)} tables")
                
                if len(tables) >= 10:
                    target_table = tables[9]  # Index 9 for the 10th table
                    print("Found target table!")
                    
                    # Get table HTML
                    table_html = target_table.get_attribute('outerHTML')
                    
                    # Convert to DataFrame
                    df = pd.read_html(table_html)[0]

                    header_values = list(df.columns)
                    df = df[~df.apply(lambda row: all(str(val) in header_values for val in row), axis=1)]
                    # print(f"Table shape: {df.shape}")
                    # print("Columns:", list(df.columns))
                    
                    return df
                else:
                    print(f"Not enough tables found. Only found {len(tables)} tables.")
                    return None
                    
            except Exception as e:
                print(f"Error processing page: {str(e)}")
                return None
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"Error initializing driver: {str(e)}")
            return None

    def get_tables(self):
        print("Starting to get tables...")
        df = None

        for season in self.seasons:
            try:
                df_temp = self.scrape_website(season)
                if df_temp is None:
                    print(f"Skipping season {season} due to scraping error")
                    continue

                df_temp['season'] = season
                print(f"Successfully processed season {season}")

                if df is None:
                    df = df_temp
                else:
                    df = pd.concat([df, df_temp])

                # Add delay between seasons
                delay = random.uniform(5, 10)
                print(f"Waiting {delay:.2f} seconds before next season...")
                time.sleep(delay)

            except Exception as e:
                print(f"Error processing season {season}: {str(e)}")
                continue

        if df is None:
            raise Exception("Failed to retrieve any data from all seasons")

        return df
    

    def process_data(self):
            df = self.get_tables()

            # print(df.head())

            df['Status'] = df['Score'].apply(lambda x: 'no' if pd.isna(x) else 'yes')
            df['H.team'] = df['Home']
            df['A.team'] = df['Away']
            df['H.xg'] = df['xG']
            df['A.xg'] = df['xG.1']
            df['H.xga'] = df['xG.1']
            df['A.xga'] = df['xG']
            # print(df['Score'].unique())
            # print(df.loc[df['Score']=='Score'])
            df['H.goals'] = df['Score'].apply(lambda x: None if pd.isna(x) else int(x.split('–')[0]) )
            df['A.goals'] = df['Score'].apply(lambda x: None if pd.isna(x) else int(x.split('–')[1]) )
            df['Result'] = df['Score'].apply(lambda x: None if pd.isna(x) else 3 if x.split('–')[0] > x.split('–')[1] else 1 if x.split('–')[0] == x.split('–')[1] else 0)
            

            features = ['Date', 'Day','Time', 'Result', 'H.team', 'A.team', 'H.xg', 'A.xg', 'H.xga', 'A.xga', 'H.goals', 'A.goals', 'Status']

            return df[features]


    def feature_engineering(self):

        df = self.process_data()

        # Rolling Averages
        home_df = df[['H.team', 'A.team','H.xg', 'H.xga', 'H.goals', 'A.goals', 'Date',  'Status' ,'Result']].copy()
        away_df = df[['A.team', 'H.team','A.xg', 'A.xga', 'A.goals', 'H.goals', 'Date', 'Status', 'Result']].copy()
        away_df['Result_True'] = away_df['Result'].apply(lambda x: 3 if x ==0 else 0 if x==3 else 1)
        away_df.drop(columns=['Result'], inplace=True)

        home_df.columns = ['Team', 'Opponent', 'xg', 'xga', 'goals', 'opponent_goals', 'Date', 'Status', 'Result']
        away_df.columns = ['Team', 'Opponent', 'xg', 'xga', 'goals', 'opponent_goals', 'Date', 'Status', 'Result']
        home_df['location'] = 'home'
        away_df['location'] = 'away'

        both_df = pd.concat([home_df, away_df])
        team_df = home_df.copy()

        team_df = team_df.sort_values(['Team', 'Date'])
        team_df = team_df.groupby('Team', group_keys=False).apply(lambda x: x)

        team_df['rolling_xg'] = team_df['xg'].shift().rolling(window=5, min_periods=1).mean()
        team_df['rolling_xga'] = team_df['xga'].shift().rolling(window=5, min_periods=1).mean()

        # print(team_df.head())

        team_df['rolling_xg_diff'] = team_df.apply(lambda row: row['rolling_xg'] - row['goals'], axis=1)
        team_df['rolling_xga_diff'] = team_df.apply(lambda row: row['rolling_xga'] - row['opponent_goals'], axis=1)

        team_df['form_rolling_5'] = team_df['Result'].shift().rolling(window=5, min_periods=1).mean()
        team_df['form_rolling_10'] = team_df['Result'].shift().rolling(window=10, min_periods=1).mean()

        team_df['opponent_form_rolling_3'] = team_df['Result'].shift().rolling(window=3, min_periods=1).mean()
        team_df['opponent_form_rolling_6'] = team_df['Result'].shift().rolling(window=6, min_periods=1).mean()

        flat_df = both_df.copy()
        flat_df = flat_df.sort_values(['Team', 'Opponent', 'location','Date'])
        both_df = flat_df.groupby(['Team', 'Opponent', 'location'], 
                            group_keys=False, 
                            ).apply(lambda x: x)

        both_df['opponent_home_form_rolling_2'] = both_df['Result'].shift().rolling(window=2, min_periods=1).mean()
        both_df['opponent_away_form_rolling_2'] = both_df['Result'].shift().rolling(window=2, min_periods=1).mean()

        team_df.reset_index( inplace=True)
        team_df.sort_values(['Date', 'index'], inplace=True)


        return team_df
    
    def get_data(self):
        df = self.feature_engineering()
        return df


    def export_to_database(self, df):
        max_retries = 5
        retry_delay = 5  # seconds
        
        # print("\n=== Database Export Debug ===")
        # print(f"DataFrame shape: {df.shape}")
        # print(f"DataFrame columns: {df.columns.tolist()}")
        # print("\nDatabase config (password hidden):")
        # debug_config = dict(self.db_config)
        # debug_config['password'] = '****'
        # print(debug_config)
        
        for attempt in range(max_retries):
            try:
                print(f"\nAttempt {attempt + 1} of {max_retries}")
                
                # Create engine with echo=True for SQL logging
                engine = create_engine(
                    f"postgresql://{self.db_config['user']}:{self.db_config['password']}@"
                    f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}",
                    echo=True  # This will log all SQL statements
                )
                
                # Test connection
                print("Testing database connection...")
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1")).scalar()
                    print(f"Connection test result: {result}")
                
                # Try operations one at a time
                print("\nInserting teams...")
                self.insert_teams(df, engine)
                print("Teams inserted successfully")
                
                print("\nInserting matches...")
                self.insert_matches(df, engine)
                print("Matches inserted successfully")
                
                print("\nData export completed successfully")
                break
                
            except Exception as e:
                print(f"\nError during attempt {attempt + 1}:")
                # print(f"Error type: {type(e).__name__}")
                # print(f"Error message: {str(e)}")
                
                # Print full traceback
                import traceback
                # print("\nFull traceback:")
                # traceback.print_exc()
                
                if attempt == max_retries - 1:
                    print(f"\nFailed to export data after {max_retries} attempts")
                    raise
                
                print(f"\nRetrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        return True

    # def insert_teams(self, df, engine):
    #     """
    #     Inserts unique teams into teams table
    #     """
    #     # Get unique teams
    #     unique_teams = df['Team'].unique()
        
    #     teams_df = pd.DataFrame({'team_name': unique_teams})
        
    #     # Insert teams with ON CONFLICT DO NOTHING
    #     teams_df.to_sql('teams', engine, if_exists='append', index=False,
    #                    method='multi',
    #                    dtype={'team_name': String(100)})

    def insert_teams(self, df, engine):
        """
        Inserts unique teams into teams table
        """
        # Get unique teams
        unique_teams = df['Team'].unique()
        
        # Create connection
        with engine.connect() as conn:
            # Create table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS teams (
                    team_id SERIAL PRIMARY KEY,
                    team_name VARCHAR(100) UNIQUE
                )
            """))
            
            # Insert teams with ON CONFLICT
            stmt = text("""
                INSERT INTO teams (team_name)
                VALUES (:team_name)
                ON CONFLICT (team_name) DO NOTHING
            """)
            
            # Execute for each team
            for team in unique_teams:
                conn.execute(stmt, {"team_name": team})
            
            conn.commit()


    # def insert_matches(self, df, engine):
    #     """
    #     Inserts matches data into matches table
    #     """
    #     # Create connection
    #     with engine.connect() as conn:
    #         # Get team_id mapping
    #         team_mapping = pd.read_sql(
    #             "SELECT team_id, team_name FROM teams",
    #             conn
    #         ).set_index('team_name')['team_id'].to_dict()

    #         # Prepare matches data
    #         matches_df = df.copy()
    #         matches_df['home_team_id'] = matches_df['Team'].map(team_mapping)
    #         matches_df['away_team_id'] = matches_df['Opponent'].map(team_mapping)
            
    #         # Convert date format if needed
    #         matches_df['Date'] = pd.to_datetime(matches_df['Date'])

    #         # Select and rename columns for database
    #         matches_for_db = matches_df[[
    #             'Date', 'home_team_id', 'away_team_id', 
    #             'goals', 'opponent_goals', 'xg', 'xga',
    #             'Status', 'rolling_xg', 'rolling_xga',
    #             'form_rolling_5', 'form_rolling_10'
    #         ]].copy()

    #         matches_for_db.columns = [
    #             'match_date', 'home_team_id', 'away_team_id',
    #             'goals', 'opponent_goals', 'xg', 'xga',
    #             'status', 'rolling_xg', 'rolling_xga',
    #             'form_5', 'form_10'
    #         ]

    #         # Insert matches with ON CONFLICT DO UPDATE
    #         matches_for_db.to_sql(
    #             'matches',
    #             conn,
    #             if_exists='append',
    #             index=False,
    #             method='multi',
    #             dtype={
    #                 'match_date': DateTime,
    #                 'home_team_id': Integer,
    #                 'away_team_id': Integer,
    #                 'goals': Float,
    #                 'opponent_goals': Float,
    #                 'xg': Float,
    #                 'xga': Float,
    #                 'status': String(20),
    #                 'rolling_xg': Float,
    #                 'rolling_xga': Float,
    #                 'form_5': Float,
    #                 'form_10': Float
    #             },
    #         )

    def insert_matches(self, df, engine):
        """
        Inserts matches data into matches table
        """
        # Create connection
        with engine.connect() as conn:
            # Create table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS matches (
                    match_id SERIAL PRIMARY KEY,
                    match_date TIMESTAMP NOT NULL,
                    home_team_id INTEGER REFERENCES teams(team_id),
                    away_team_id INTEGER REFERENCES teams(team_id),
                    home_score FLOAT,
                    away_score FLOAT,
                    home_xg FLOAT,
                    away_xg FLOAT,
                    status VARCHAR(20),
                    rolling_xg FLOAT,
                    rolling_xga FLOAT,
                    form_5 FLOAT,
                    form_10 FLOAT,
                    UNIQUE (match_date, home_team_id, away_team_id)
                )
            """))
                
            # Get team_id mapping - Fixed this query
            team_mapping = pd.read_sql(
                text("SELECT team_id, team_name FROM teams"),
                conn
            ).set_index('team_name')['team_id'].to_dict()
            
            # print("Team mapping:", team_mapping)  # Debug print

            # Insert matches with ON CONFLICT
            stmt = text("""
                INSERT INTO matches (
                    match_date, home_team_id, away_team_id,
                    home_score, away_score, home_xg, away_xg,
                    status, rolling_xg, rolling_xga,
                    form_5, form_10
                )
                VALUES (
                    :match_date, :home_team_id, :away_team_id,
                    :home_score, :away_score, :home_xg, :away_xg,
                    :status, :rolling_xg, :rolling_xga,
                    :form_5, :form_10
                )
                ON CONFLICT (match_date, home_team_id, away_team_id) 
                DO UPDATE SET
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    home_xg = EXCLUDED.home_xg,
                    away_xg = EXCLUDED.away_xg,
                    status = EXCLUDED.status,
                    rolling_xg = EXCLUDED.rolling_xg,
                    rolling_xga = EXCLUDED.rolling_xga,
                    form_5 = EXCLUDED.form_5,
                    form_10 = EXCLUDED.form_10
                )
            """)

            # Debug print before processing
            # print("\nFirst few rows of DataFrame:")
            # print(df[['Date', 'Team', 'Opponent']].head())

            # Prepare and execute for each match
            for _, row in df.iterrows():
                try:
                    match_data = {
                        "match_date": pd.to_datetime(row['Date']),
                        "home_team_id": team_mapping.get(row['Team']),
                        "away_team_id": team_mapping.get(row['Opponent']),
                        "home_score": row['goals'],
                        "away_score": row['opponent_goals'],
                        "home_xg": row['xg'],
                        "away_xg": row['xga'],
                        "status": row['Status'],
                        "rolling_xg": row['rolling_xg'],
                        "rolling_xga": row['rolling_xga'],
                        "form_5": row['form_rolling_5'],
                        "form_10": row['form_rolling_10']
                    }
                    
                    # Debug print for each row
                    # print(f"\nProcessing match: {row['Team']} vs {row['Opponent']}")
                    # print(f"Team IDs: {match_data['home_team_id']} vs {match_data['away_team_id']}")
                    
                    conn.execute(stmt, match_data)
                except Exception as e:
                    # print(f"Error processing row: {row}")
                    # print(f"Error: {str(e)}")
                    continue

            conn.commit()

    def check_database_connection(self):
        """
        Checks if the database is accessible and returns connection status
        """
        try:
            engine = create_engine(
                f"postgresql://{self.db_config['user']}:{self.db_config['password']}@"
                f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            )
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                return True
        except Exception as e:
            print(f"Database connection failed: {str(e)}")
            return False

    def verify_data_update(self, df):
        """
        Verifies that the data was actually inserted into the database
        """
        try:
            engine = create_engine(
                f"postgresql://{self.db_config['user']}:{self.db_config['password']}@"
                f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            )
            with engine.connect() as conn:
                # Check if matches table exists
                table_exists = conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'matches')"
                )).scalar()
                
                if not table_exists:
                    print("Matches table does not exist!")
                    return False
                
                # Count total matches in database
                db_count = conn.execute(text("SELECT COUNT(*) FROM matches")).scalar()
                
                # Get the most recent date in database
                latest_date = conn.execute(text(
                    "SELECT MAX(match_date) FROM matches"
                )).scalar()
                
                print(f"Database contains {db_count} matches")
                print(f"Most recent match date: {latest_date}")
                
                # Verify that we have data for recent matches
                if latest_date:
                    days_since_update = (datetime.now() - latest_date).days
                    print(f"Days since last update: {days_since_update}")
                    
                return db_count > 0
                
        except Exception as e:
            print(f"Verification failed: {str(e)}")
            return False

    def run_update(self):
        """
        Main method to run scraper and update database
        """
        # First check database connection
        if not self.check_database_connection():
            raise Exception("Cannot connect to database")
        
        # Get the data
        df = self.get_data()
        
        # Export to database
        self.export_to_database(df)
        
        # Verify the update
        if not self.verify_data_update(df):
            raise Exception("Data update verification failed")
        
        return "Update completed successfully"
    


def run_scraper():
    print(f"Running scraper at {datetime.now()}")
    scraper = Scraper([24])
    scraper.run_update()

if __name__ == "__main__":
    # Schedule the job
    schedule.every().day.at("00:00").do(run_scraper)
    
    # Run once at startup
    run_scraper()
    
    # Keep the script running
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)

run_scraper()


