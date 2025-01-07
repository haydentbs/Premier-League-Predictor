import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO 

class Scraper:
    def __init__(self, seasons):
        self.base_url = 'https://fbref.com/en/comps/9/'
        self.seasons = seasons

    def get_url(self, season):
        
        return f'{self.base_url}20{season}-20{season+1}/schedule/20{season}-20{season+1}-Premier-League-Scores-and-Fixtures'
        
    def scrape_website(self, season):
        # Add headers to mimic a browser request
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
        

        
        # Make the request
        response = requests.get(self.get_url(season), headers=headers)
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            return None
        
    
    
    def get_tables(self):
        # Method 1: Find table by ID

        df = None

        for season in self.seasons:
            soup = self.scrape_website(season)

            # table = soup.find('table', {'id': 'sched_2023-2024_9_1'})  # FBRef usually has specific table IDs
        
        # Method 2: Find table by class
            table = soup.find('table', {'class': 'stats_table'})
        
        # Convert to DataFrame
            if table:
                html_string = str(table)  # Convert table to string
                df_temp = pd.read_html(StringIO(html_string))[0]  # Wrap in StringIO
                df_temp['season'] = season 

            if df is None:
                df = df_temp
            else:
                df = pd.concat([df, df_temp])
                
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
        df['Result'] = df['Score'].apply(lambda x: None if pd.isna(x) else 2 if x.split('–')[0] > x.split('–')[1] else 1 if x.split('–')[0] == x.split('–')[1] else 0)
        

        features = ['Date', 'Day','Time', 'Result', 'H.team', 'A.team', 'H.xg', 'A.xg', 'H.xga', 'A.xga', 'Status']

        return df[features]


def feature_engineering(df):

    # Rolling Averages
    home_df = df[['H.team', 'A.team','H.xg', 'H.xga', 'Date', 'Result', 'Status']]
    away_df = df[['A.team', 'H.team','A.xg', 'A.xga', 'Date', 'Result', 'Status']]
    away_df['Result_True'] = away_df['Result'].apply(lambda x: 2 if x ==0 else 1 if x==1 else 0)
    away_df.drop(columns=['Result'], inplace=True)

    home_df.columns = ['Team', 'Opponent', 'xg', 'xga', 'Date', 'Result', 'Status']
    away_df.columns = ['Team', 'Opponent', 'xg', 'xga', 'Date', 'Result', 'Status']

    team_df = pd.concat([home_df, away_df])

    team_df = team_df.groupby('Team').apply(lambda x: x.sort_values('Date'))

    team_df['rolling_xg'] = team_df['xg'].rolling(window=5, min_periods=1).mean()
    team_df['rolling_xga'] = team_df['xga'].rolling(window=5, min_periods=1).mean()

    team_df['rolling_xg_diff'] = team_df['rolling_xg'] - team_df['rolling_xga']

    team_df['form_rolling_5'] = team_df['Result'].rolling(window=5, min_periods=1).mean()
    team_df['form_rolling_10'] = team_df['Result'].rolling(window=10, min_periods=1).mean()

    

    flat_df = team_df.reset_index()
    print(flat_df.head())
    team_df = flat_df.groupby(['Team', 'Opponent'])

    team_df['opponent_form_rolling_3'] = team_df['Result'].rolling(window=3, min_periods=1).mean()
    team_df['opponent_form_rolling_6'] = team_df['Result'].rolling(window=6, min_periods=1).mean()



        # df['H.xg_rolling'] = df['H.xg'].rolling(window=5).mean()
        # df['A.xg_rolling'] = df['A.xg'].rolling(window=5).mean()
        # df['H.xga_rolling'] = df['H.xga'].rolling(window=5).mean()
        # df['A.xga_rolling'] = df['A.xga'].rolling(window=5).mean()
    


    return team_df



# scraper = Scraper([22,23,24])
# table = scraper.process_data()
# table.to_csv('premier_league_data.csv', index=False)

table = pd.read_csv('premier_league_data.csv')



table = feature_engineering(table)

print(table.head())
print(table.tail())

