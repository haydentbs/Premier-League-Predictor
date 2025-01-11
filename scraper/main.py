from scraper import MatchScraper
from processor import DataProcessor
from database_handler import DatabaseHandler
import os
import pandas as pd

def run_update(config):
    # Initialize components

    if os.path.exists('data/raw_data.csv'):
        raw_data = pd.read_csv('data/raw_data.csv')

    else:
        scraper = MatchScraper(config['seasons'])
        
        
        raw_data = scraper.get_tables()
        raw_data.to_csv('data/raw_data.csv')
    
    processor = DataProcessor()
    # Process data
    df = processor.process_data(raw_data)
    processor.validate_data(df)
    
    # Update database
    db_handler = DatabaseHandler(config['database'], df)
    
    db_handler.insert_data_safe()
    
    # Verify update
    # if not db_handler.verify_update(df):
    #     raise Exception("Data update verification failed")
    
    return "Update completed successfully"

if __name__ == "__main__":
    config = {
        'seasons': [17,18,19,20,21,22,23,24],
        'database': {
            'user': 'postgres',
            'password': 'postgres',
            'host': 'db',
            'port': '5432',
            'database': 'premier_league'
        }
    }
    
    result = run_update(config)
    print(result)