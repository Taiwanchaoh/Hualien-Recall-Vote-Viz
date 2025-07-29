#!/usr/bin/env python3
"""
Data parsing script for recall vote data from CEC website.
Extracts voting data for all districts and polling stations in Hualien County.
"""

import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RecallVoteDataParser:
    """Parser for recall vote data from CEC website."""
    
    def __init__(self, headless=True, test_mode=False, max_districts=2, max_stations_per_district=3):
        """Initialize the parser with webdriver setup."""
        self.url = "https://recallvote.cec.gov.tw/voteResult.html?caseNo=A21"
        self.driver = None
        self.headless = headless
        self.data = []
        self.csv_filename = "./data/recall_vote_data_detailed.csv"
        self.json_filename = "./data/recall_vote_data_detailed.json"
        
        # Test mode settings
        self.test_mode = test_mode
        self.max_districts = max_districts
        self.max_stations_per_district = max_stations_per_district
        
    def setup_driver(self):
        """Set up Chrome webdriver with appropriate options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def load_existing_data(self):
        """Load existing data from CSV file if it exists."""
        if os.path.exists(self.csv_filename):
            try:
                df = pd.read_csv(self.csv_filename)
                self.data = df.to_dict('records')
                logger.info(f"Loaded {len(self.data)} existing records from {self.csv_filename}")
                return True
            except Exception as e:
                logger.warning(f"Could not load existing data: {e}")
        return False
        
    def save_data_incrementally(self):
        """Save data incrementally to avoid losing progress."""
        if self.data:
            df = pd.DataFrame(self.data)
            df.to_csv(self.csv_filename, index=False, encoding='utf-8-sig')
            with open(self.json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.data)} records incrementally")
        
    def get_district_list(self):
        """Get list of all districts in Hualien County."""
        try:
            # Wait for the district list to load
            district_elements = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#kh-area-list li"))
            )
            
            districts = []
            for element in district_elements:
                district_name = element.text.strip()
                dept_code = element.get_attribute("deptcode")
                districts.append({
                    "name": district_name,
                    "code": dept_code
                })
            
            # Limit districts in test mode
            if self.test_mode:
                districts = districts[:self.max_districts]
                logger.info(f"TEST MODE: Limited to {len(districts)} districts: {[d['name'] for d in districts]}")
            else:
                logger.info(f"Found {len(districts)} districts: {[d['name'] for d in districts]}")
            
            return districts
            
        except Exception as e:
            logger.error(f"Error getting district list: {e}")
            return []
    
    def get_polling_stations_for_district(self, district_element):
        """Get list of polling stations for a specific district."""
        try:
            # Click on the district to load its polling stations
            district_element.click()
            time.sleep(1)  # Reduced wait time
            
            # Wait for polling station selector to appear
            polling_station_select = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "vote-area-seletor"))
            )
            
            # Get all options from the dropdown
            options = polling_station_select.find_elements(By.TAG_NAME, "option")
            
            polling_stations = []
            for option in options:
                station_name = option.text.strip()
                station_value = option.get_attribute("value")
                if station_name and station_value:  # Skip empty options
                    polling_stations.append({
                        "name": station_name,
                        "value": station_value
                    })
            
            # Limit polling stations in test mode
            if self.test_mode:
                polling_stations = polling_stations[:self.max_stations_per_district]
                logger.info(f"TEST MODE: Limited to {len(polling_stations)} polling stations for district")
            else:
                logger.info(f"Found {len(polling_stations)} polling stations for district")
            
            return polling_stations
            
        except Exception as e:
            logger.error(f"Error getting polling stations: {e}")
            return []
    
    def extract_voting_data(self):
        """Extract voting data from the current page."""
        try:
            # Wait for the result table to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "result-table"))
            )
            
            # Extract data from tables
            data = {}
            
            # Get agreement/disagreement votes
            agree_element = self.driver.find_element(By.CLASS_NAME, "agreeTks")
            disagree_element = self.driver.find_element(By.CLASS_NAME, "disagreeTks")
            data["同意罷免票數"] = agree_element.text.replace(",", "")
            data["不同意罷免票數"] = disagree_element.text.replace(",", "")
            
            # Get valid/invalid votes and total voters
            prof1_element = self.driver.find_element(By.CLASS_NAME, "prof1")
            prof2_element = self.driver.find_element(By.CLASS_NAME, "prof2")
            prof3_element = self.driver.find_element(By.CLASS_NAME, "prof3")
            data["有效票數"] = prof1_element.text.replace(",", "")
            data["無效票數"] = prof2_element.text.replace(",", "")
            data["投票人數"] = prof3_element.text.replace(",", "")
            
            # Get completed polling stations data
            prof7_element = self.driver.find_element(By.CLASS_NAME, "prof7")
            prof_rate_element = self.driver.find_element(By.CLASS_NAME, "profRate")
            data["已完成投票所投票人總數"] = prof7_element.text.replace(",", "")
            data["已完成投票所投票率(%)"] = prof_rate_element.text
            
            # Get total voters and agreement rate
            gmeb_element = self.driver.find_element(By.CLASS_NAME, "gmeb")
            ytp_rate_element = self.driver.find_element(By.CLASS_NAME, "ytpRate")
            data["投票人總數"] = gmeb_element.text.replace(",", "")
            data["同意票數佔投票人總數比率(%)"] = ytp_rate_element.text
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting voting data: {e}")
            return {}
    
    def is_data_already_extracted(self, district_name, station_name):
        """Check if data for this district and station has already been extracted."""
        for record in self.data:
            if record.get("選舉區") == district_name and record.get("投開票所名稱") == station_name:
                return True
        return False
    
    def parse_all_data(self):
        """Parse data for all districts and polling stations."""
        try:
            # Load existing data first
            self.load_existing_data()
            
            self.setup_driver()
            self.driver.get(self.url)
            logger.info("Navigated to CEC website")
            
            # Wait for page to load completely
            time.sleep(3)
            
            # Get all districts
            districts = self.get_district_list()
            
            for district in districts:
                logger.info(f"Processing district: {district['name']}")
                
                # Find and click on the district
                district_element = self.driver.find_element(
                    By.XPATH, f"//li[@deptcode='{district['code']}' and text()='{district['name']}']"
                )
                
                # Get polling stations for this district
                polling_stations = self.get_polling_stations_for_district(district_element)
                
                # Process each polling station
                for station in polling_stations:
                    # Skip if already extracted
                    if self.is_data_already_extracted(district['name'], station['name']):
                        logger.info(f"Skipping {station['name']} - already extracted")
                        continue
                    
                    logger.info(f"Processing polling station: {station['name']}")
                    
                    try:
                        # Select the polling station from dropdown
                        polling_station_select = self.driver.find_element(By.ID, "vote-area-seletor")
                        self.driver.execute_script(
                            f"arguments[0].value = '{station['value']}';", 
                            polling_station_select
                        )
                        
                        # Trigger change event
                        self.driver.execute_script(
                            "arguments[0].dispatchEvent(new Event('change'));", 
                            polling_station_select
                        )
                        
                        # Wait for data to update
                        time.sleep(2)  # Reduced wait time
                        
                        # Extract voting data
                        voting_data = self.extract_voting_data()
                        
                        if voting_data:
                            # Combine all data
                            row_data = {
                                "選舉區": district['name'],
                                "投開票所名稱": station['name'],
                                **voting_data
                            }
                            self.data.append(row_data)
                            logger.info(f"Successfully extracted data for {station['name']}")
                            
                            # Save incrementally every 10 records
                            if len(self.data) % 10 == 0:
                                self.save_data_incrementally()
                        
                    except Exception as e:
                        logger.error(f"Error processing polling station {station['name']}: {e}")
                        continue
                
                # Save after each district
                self.save_data_incrementally()
                
                # Small delay between districts
                time.sleep(1)
            
            logger.info(f"Total records extracted: {len(self.data)}")
            return self.data
            
        except Exception as e:
            logger.error(f"Error in parse_all_data: {e}")
            # Save any data we have before exiting
            self.save_data_incrementally()
            return self.data
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_to_csv(self, filename=None):
        """Save extracted data to CSV file."""
        if not self.data:
            logger.warning("No data to save")
            return
        
        if filename is None:
            filename = self.csv_filename
            
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Data saved to {filename}")
        return df
    
    def save_to_json(self, filename=None):
        """Save extracted data to JSON file."""
        if not self.data:
            logger.warning("No data to save")
            return
        
        if filename is None:
            filename = self.json_filename
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        logger.info(f"Data saved to {filename}")

def main():
    """Main function to run the data parser."""
    logger.info("Starting recall vote data extraction...")
    
    # Create parser instance for full extraction
    parser = RecallVoteDataParser(headless=True, test_mode=False)
    
    # Parse all data
    data = parser.parse_all_data()
    
    if data:
        # Save to files
        df = parser.save_to_csv()
        parser.save_to_json()
        
        # Display summary
        logger.info("Data extraction completed successfully!")
        logger.info(f"Total records: {len(data)}")
        logger.info(f"Districts covered: {df['選舉區'].nunique()}")
        logger.info(f"Polling stations covered: {df['投開票所名稱'].nunique()}")
        
        # Display first few rows
        print("\nFirst few records:")
        print(df.head())
        
        # Display data structure
        print("\nData structure:")
        print(df.columns.tolist())
        print(f"\nSample data for first record:")
        if len(data) > 0:
            for key, value in data[0].items():
                print(f"  {key}: {value}")
        
    else:
        logger.error("No data was extracted")

if __name__ == "__main__":
    main() 