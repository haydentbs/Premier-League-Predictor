import pandas as pd
import pandas as pd
from datetime import datetime

class DataProcessor:
    def __init__(self):
        pass
    
    def sort_data(self, df):

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


    def process_data(self, df):

        df = self.sort_data(df)

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

        team_df['Date'] = pd.to_datetime(team_df['Date'])

        print(team_df.head())
        print(team_df.columns)


        return team_df
    
    def validate_data(self, df):
        """
        Validates processed data before database insertion
        """
        required_columns = ['Date', 'Result']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
        return True