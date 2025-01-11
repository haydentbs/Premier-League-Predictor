from data_import import pandas_from_api
import os
import pandas as pd
import matplotlib.pyplot as plt
from data_processing import DataProcessing
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_squared_error, r2_score
import seaborn as sns
import numpy as np


class ModelTrain:
    def __init__(self):
        self.df = self.import_data()

    def import_data(self):
        if os.path.exists('data.csv'):
            df = pd.read_csv('data.csv')
        else:
            df = pandas_from_api('http://localhost:5001/matches')
            df.to_csv('data.csv', index=False)
        return df
    
    def create_training_data(self,df):

        processing = DataProcessing(df)
        training_data, features, self.label_encoders = processing.create_training_data()
        # print(training_data.head())
        # print(df.head())
        X = training_data[features]
        y = training_data['result']

        return train_test_split(X, y, train_size=0.7, test_size=0.3)


    def train(self):

        data = self.import_data()

        # print(data.isna().sum())
        X_train, X_test, y_train, y_test = self.create_training_data(data)

        model =  LogisticRegression()

        # print(y_train)

        model.fit(X_train, y_train)
        y_pred  = model.predict(X_test)

        print("Coefficients: \n", model.coef_)
        # The mean squared error
        print("Mean squared error: %.2f" % mean_squared_error(y_test, y_pred))
        # The coefficient of determination: 1 is perfect prediction
        print("Coefficient of determination: %.2f" % r2_score(y_test, y_pred))

        comparison_dataset = X_test.copy()
        comparison_dataset['result'] = y_test
        comparison_dataset['prediction'] = y_pred
        # print(comparison_dataset.head())

        self.model = model

        return comparison_dataset

    def metrics(self, results):

        metric_values = {}
        metric_values['incorrect_predictions'] = {}
        metric_values['total_games'] = {}

        metric_values['prediction_actual'] = {}

        miss = len(results[results['result'] != results['prediction']])
        total = 1 - len(results['result'])

        print('Success rate: ', miss/total)

        for team in self.df['team'].unique():

            team_index = self.label_encoders['team'].transform([team])
        
            team_data = results[results['team'] == team_index[0]]
            misses = team_data[team_data['result'] != team_data['prediction']]

            metric_values['incorrect_predictions'][team] = len(misses)
            metric_values['total_games'][team] = len(team_data['result'])

            metric_values['prediction_actual'][team] = [[misses['prediction'],misses['result']]]


            print(team)
            print(len(misses), '/', len(team_data['result']),'\n')

        print(len(results['result']))
        print(len(results['prediction']))

        return metric_values, results, self.model
    

class VisualiseMetrics():

    def __init__(self, metric_data, results, model):
        self.metric_data = metric_data
        self.results = results
        self.model = model


    def bar_percentage(self):

        fig, (ax1) = plt.subplots(1, 1, figsize=(12, 5))

        print(self.metric_data['prediction_actual']['Watford'])

        percentage_correct = []
        team_names = []

        for team in self.metric_data['incorrect_predictions'].keys():
            percentage_correct.append(1-(self.metric_data['incorrect_predictions'][team]/self.metric_data['total_games'][team]))
            team_names.append(team)

        ax1.bar(team_names,percentage_correct)
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=30, ha='right')
        ax1.set_ylim(0.6,1.1)
        plt.draw()
        
        plt.savefig('figures/team_bar_percentage.png')

    def confusion_matrix(self):

        comparison = self.results[['result', 'prediction']].copy()
        comparison_counts = comparison.value_counts().reset_index(name='count')
        comparison_counts = comparison.value_counts().unstack(fill_value=0)

        # Display the confusion matrix
        plt.figure(figsize=(8, 6))
        sns.heatmap(comparison_counts, annot=True, fmt='d', cmap='Blues', cbar=False)
        plt.title('Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.savefig('figures/confusion.png')
        print(comparison_counts)

    def feature_importance(self):
        coefficients = self.model.coef_[0]
        odds_ratios = np.exp(coefficients)

        X = self.results.drop(columns=['result', 'prediction'])

        # Display feature importance using coefficients and odds ratios
        feature_importance = pd.DataFrame({
            'Feature': X.columns,
            'Coefficient': coefficients,
            'Odds Ratio': odds_ratios
        })
        print("\nFeature Importance (Coefficient and Odds Ratio):")
        print(feature_importance.sort_values(by='Coefficient', ascending=False))



# MSE=0.57, R2=0.27


def main():
    Train = ModelTrain()
    data = Train.train()
    metric_values, results, model = Train.metrics(data)
    Visualise = VisualiseMetrics(metric_values, results, model)
    Visualise.bar_percentage()
    Visualise.confusion_matrix()
    Visualise.feature_importance()

    # Train.visualise_metrics(metric_values)

main()





# def randoms():
    
#     keys = df.columns
#     print(keys)

#     float_cols = [col for col in df.columns if df[col].dtype == 'float64']
#     float_cols.append('result')
#     print(float_cols)

#     corr = df[float_cols].corr()

#     plt.matshow(corr)
#     plt.colorbar()
#     plt.title('Correlation Matrix')
#     plt.xticks(range(len(float_cols)), float_cols, rotation=45, ha='left')
#     plt.yticks(range(len(float_cols)), float_cols)

#     plt.show()




    # print(df.head())