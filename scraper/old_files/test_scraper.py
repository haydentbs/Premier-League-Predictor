from scraper import Scraper
import sys

def test_scraping():
    scraper = Scraper([23])  # Test with just one season
    soup = scraper.scrape_website(23)
    
    if soup is not None:
        print("Successfully retrieved and parsed the page!")
        return True
    else:
        print("Failed to retrieve or parse the page.")
        return False

if __name__ == "__main__":
    success = test_scraping()
    sys.exit(0 if success else 1)