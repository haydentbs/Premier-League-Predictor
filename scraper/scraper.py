from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import random

class MatchScraper:
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
                delay = random.uniform(0, 1)
                print(f"Waiting {delay:.2f} seconds before next season...")
                time.sleep(delay)

            except Exception as e:
                print(f"Error processing season {season}: {str(e)}")
                continue

        if df is None:
            raise Exception("Failed to retrieve any data from all seasons")

        return df