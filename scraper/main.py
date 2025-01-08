from scraper import MatchScraper
from processor import DataProcessor
from database_handler import DatabaseHandler

def run_update(config):
    # Initialize components
    scraper = MatchScraper(config['seasons'])
    processor = DataProcessor()
    
    
    # Check database connection
    
    
    # Scrape data
    raw_data = scraper.get_tables()
    
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
        'seasons': [23],
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