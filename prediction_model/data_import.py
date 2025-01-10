import requests
import pandas as pd

def pandas_from_api(url):
    response = requests.get(url)
    df = pd.DataFrame(response.json())
    return df

