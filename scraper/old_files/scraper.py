import os
import time
from datetime import datetime
import schedule
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO 

import psycopg2
from sqlalchemy import create_engine, String, Integer, Float, DateTime, text
import random
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import sys
from fake_useragent import UserAgent

class Scraper:
    def __init__(self, seasons):
        self.base_url = 'https://fbref.com/en/comps/9/'
        self.seasons = seasons
        
        # Initialize User-Agent rotator
        self.ua = UserAgent()
        
        # Configure session with retries and backoff
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        # List of backup User-Agents if fake_useragent fails
        self.backup_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'db'),
            'database': os.getenv('POSTGRES_DB', 'premier_league'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }

    def get_url(self, season):
        
        return f'{self.base_url}20{season}-20{season+1}/schedule/20{season}-20{season+1}-Premier-League-Scores-and-Fixtures'
        
    def get_headers(self):
        """Get random headers for each request"""
        try:
            user_agent = self.ua.random
        except:
            user_agent = random.choice(self.backup_agents)
        
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def scrape_website(self, season):
        try:
            print(f"Scraping season {season}...")
            
            # Add longer random delay between requests
            delay = random.uniform(10, 15)
            print(f"Waiting {delay:.2f} seconds before request...")
            time.sleep(delay)
            
            # Get fresh headers for each request
            headers = self.get_headers()
            print(f"Using User-Agent: {headers['User-Agent']}")
            
            # Make the request using session
            url = self.get_url(season)
            print(f"Requesting URL: {url}")
            
            response = self.session.get(
                url, 
                headers=headers,
                timeout=30
            )
            
            print(f"Status code for season {season}: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                if soup is None:
                    print(f"Failed to parse HTML for season {season}")
                    return None
                print(f"Successfully scraped season {season}")
                return soup
            elif response.status_code == 429:
                print(f"Rate limited. Waiting 180 seconds...")
                time.sleep(180)  # Increased wait time
                return self.scrape_website(season)  # Retry
            else:
                print(f"Failed to retrieve the page. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error scraping season {season}: {str(e)}")
            return None
        
    
    
    def get_tables(self):
        print("Starting to get tables...")
        df = None

        for season in self.seasons:
            try:
                soup = self.scrape_website(season)
                if soup is None:
                    print(f"Skipping season {season} due to scraping error")
                    continue

                # Find table
                table = soup.find('table', {'class': 'stats_table'})
                if table is None:
                    print(f"No table found for season {season}")
                    continue

                # Convert to DataFrame
                html_string = str(table)
                df_temp = pd.read_html(StringIO(html_string))[0]
                df_temp['season'] = season
                print(f"Successfully processed season {season}")

                if df is None:
                    df = df_temp
                else:
                    df = pd.concat([df, df_temp])

            except Exception as e:
                print(f"Error processing season {season}: {str(e)}")
                continue

        if df is None:
            raise Exception("Failed to retrieve any data from all seasons")

        return df
    
    def process_data(self):
        df = self.get_tables()

        df['Status'] = df['Score'].apply(lambda x: 'no' if pd.isna(x) else 'yes')
        df['H.team'] = df['Home']
        df['A.team'] = df['Away']
        df['H.xg'] = df['xG']
        df['A.xg'] = df['xG.1']
        df['H.xga'] = df['xG.1']
        df['A.xga'] = df['xG']
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

        print(team_df.head())

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
        
        for attempt in range(max_retries):
            try:
                engine = create_engine(
                    f"postgresql://{self.db_config['user']}:{self.db_config['password']}@"
                    f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
                )
                
                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                # If connection successful, proceed with data export
                self.insert_teams(df, engine)
                self.insert_matches(df, engine)
                print("Data successfully exported to database")
                break
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to connect to database after {max_retries} attempts")
                    raise
                print(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

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

            # Get team_id mapping
            team_mapping = pd.read_sql(
                "SELECT team_id, team_name FROM teams",
                conn
            ).set_index('team_name')['team_id'].to_dict()

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
            """)

            # Prepare and execute for each match
            for _, row in df.iterrows():
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
                conn.execute(stmt, match_data)

            conn.commit()

    def run_update(self):
        """
        Main method to run scraper and update database
        """
        # Get the data
        df = self.get_data()
        
        # Export to database
        self.export_to_database(df)
        
        return "Update completed successfully"
    


def run_scraper():
    print(f"Running scraper at {datetime.now()}")
    scraper = Scraper([23,24])
    scraper.run_update()

if __name__ == "__main__":
    # Schedule the job
    schedule.every().day.at("00:00").do(run_scraper)
    
    # Run once at startup
    run_scraper()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

run_scraper()


