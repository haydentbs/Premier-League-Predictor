from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder

class DataProcessing:
    def __init__(self, df):
        self.df = df
        self.label_encoders = {}

    def remove_future_games(self):
        self.df = self.df[self.df['status_of_match'] == 'yes']
        # print(len(self.df['team']))
        self.df.dropna(inplace=True)
        return self.df
    
    def process_numerical_columns(self):

        # float_cols = [col for col in self.df.columns if self.df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
        # self.df = self.df[float_cols]

        robust_columns = ['form_rolling_5', 'form_rolling_10','rolling_xg_diff','rolling_xga_diff','opponent_form_rolling_3','opponent_form_rolling_6']
        robust = RobustScaler()
        self.df[robust_columns] = robust.fit_transform(self.df[robust_columns])
        return self.df
        

    def process_categorical_columns(self):

        columns = ['result', 'team', 'opponent']
        for col in columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    self.df[col] = self.label_encoders[col].fit_transform(self.df[col])
                else:
                    self.df[col] = self.label_encoders[col].transform(self.df[col])
        return self.df
    

    def create_training_data(self):
        print(self.df['team'].unique())
        data = self.df.copy()
        data = self.remove_future_games()
        data = self.process_numerical_columns()
        data = self.process_categorical_columns()
        # print(data.head())

        features =['form_rolling_5', 'form_rolling_10','rolling_xg_diff','rolling_xga_diff','opponent_form_rolling_3','opponent_form_rolling_6','team','opponent']
        return data, features, self.label_encoders



