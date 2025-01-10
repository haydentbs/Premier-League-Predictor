from data_import import pandas_from_api
import os
import pandas as pd
import matplotlib.pyplot as plt
from data_processing import DataProcessing
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_squared_error, r2_score


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
        training_data, features = processing.create_training_data()
        print(training_data.head())
        print(df.head())
        X = training_data[features]
        y = training_data['result']

        return train_test_split(X, y, train_size=0.7, test_size=0.3)


    def train(self):

        data = self.import_data()

        print(data.isna().sum())
        X_train, X_test, y_train, y_test = self.create_training_data(data)

        model =  LogisticRegression()

        print(y_train)

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
        print(comparison_dataset.head())

# MSE=0.57, R2=0.27


def main():
    Train = ModelTrain()
    Train.train()

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