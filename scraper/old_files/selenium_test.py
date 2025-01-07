from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import pandas as pd

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    return webdriver.Chrome(options=chrome_options)

def analyze_tables(url):
    print(f"\nAnalyzing tables for URL: {url}")
    driver = setup_driver()
    
    try:
        print("Loading page...")
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to load
        
        # First, let's look at all elements with 'table' tag
        print("\n1. All Table Elements:")
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Found {len(tables)} table elements")
        
        # Look for specific table IDs
        print("\n2. Tables with IDs:")
        tables_with_ids = driver.find_elements(By.CSS_SELECTOR, "table[id]")
        for table in tables_with_ids:
            print(f"Table ID: {table.get_attribute('id')}")
        
        # Check for tables within specific divs
        print("\n3. Tables within divs:")
        div_tables = driver.find_elements(By.CSS_SELECTOR, "div > table")
        for table in div_tables:
            parent_div = table.find_element(By.XPATH, "./..")
            print(f"Table in div: {parent_div.get_attribute('id') or parent_div.get_attribute('class')}")
        
        # Analyze table contents
        print("\n4. Table Contents Analysis:")
        for idx, table in enumerate(tables):
            print(f"\nTable {idx + 1}:")
            try:
                # Get headers
                headers = table.find_elements(By.TAG_NAME, "th")
                if headers:
                    print("Headers:", [header.text for header in headers[:5]], "...")
                
                # Get first row
                rows = table.find_elements(By.TAG_NAME, "tr")
                if len(rows) > 1:
                    first_row = rows[1]  # Skip header row
                    cells = first_row.find_elements(By.TAG_NAME, "td")
                    print("First row:", [cell.text for cell in cells[:5]], "...")
                
                # Try to convert to pandas DataFrame
                html = table.get_attribute('outerHTML')
                df = pd.read_html(html)[0]
                print(f"DataFrame shape: {df.shape}")
                print("Columns:", list(df.columns)[:5], "...")
                
            except Exception as e:
                print(f"Error analyzing table: {str(e)}")
        
        # Look for specific elements we're interested in
        print("\n5. Looking for specific schedule table:")
        try:
            schedule_div = driver.find_element(By.CSS_SELECTOR, "#div_sched_2023-2024_9")
            print("Found schedule div!")
            schedule_table = schedule_div.find_element(By.TAG_NAME, "table")
            print("Schedule table headers:", [th.text for th in schedule_table.find_elements(By.TAG_NAME, "th")[:5]])
        except Exception as e:
            print(f"Couldn't find schedule table: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test URL
    url = 'https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures'
    success = analyze_tables(url)
    print("\nAnalysis complete!")
    print(f"Success: {success}")