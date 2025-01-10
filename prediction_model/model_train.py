from data_import import pandas_from_api
import os
import pandas as pd
import matplotlib.pyplot as plt

if os.path.exists('data.csv'):
    df = pd.read_csv('data.csv')
else:
    df = pandas_from_api('http://localhost:5001/matches')
    df.to_csv('data.csv', index=False)

keys = df.columns
print(keys)

float_cols = [col for col in df.columns if df[col].dtype == 'float64']
float_cols.append('result')
print(float_cols)

corr = df[float_cols].corr()

plt.matshow(corr)
plt.colorbar()
plt.title('Correlation Matrix')
plt.xticks(range(len(float_cols)), float_cols, rotation=45, ha='left')
plt.yticks(range(len(float_cols)), float_cols)

plt.show()




print(df.head())