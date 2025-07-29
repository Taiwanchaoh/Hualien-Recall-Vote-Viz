#!/usr/bin/env python3
"""
Polling Station Location Parser
Extracts polling station locations from CEC website with Google Geocoding
"""

import time
import json
import os
from typing import List, Dict, Optional, Tuple
import pandas as pd
import googlemaps
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables
load_dotenv('.env')


class PollingStationParser:
    def __init__(self):
        self.base_url = "https://polling.cec.gov.tw/home.html?id=16"
        self.driver = None
        self.data = []
        self.gmaps = None
        self.setup_geocoding()
        
    def setup_geocoding(self):
        """Setup Google Geocoding API client"""
        api_key = os.getenv('GOOGLE_GEOCODER_API_KEY')
        if api_key:
            self.gmaps = googlemaps.Client(key=api_key)
            print("✓ Google Geocoding API client initialized")
        else:
            print("⚠ No Google Maps API key found - geocoding will be skipped")
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            
    @lru_cache(maxsize=5000)
    def geocode_address(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode an address using Google Geocoding API"""
        if not self.gmaps:
            return None, None
            
        result = self.gmaps.geocode(address)
        if result:
            location = result[0]['geometry']['location']
            return location['lat'], location['lng']
        return None, None
            
    def identify_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Identify duplicate records based on address AND station number
        Returns: (unique_records, duplicate_records)
        """
        # Find duplicates based on address AND station number
        duplicates = df[df.duplicated(subset=['address', 'number'], keep=False)]
        unique_records = df.drop_duplicates(subset=['address', 'number'], keep='first')
        
        print(f"Found {len(duplicates)} duplicate records out of {len(df)} total records")
        print(f"Unique records: {len(unique_records)}")
        
        return unique_records, duplicates
        
    def geocode_unique_addresses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add coordinates to unique addresses"""
        if not self.gmaps:
            print("⚠ Skipping geocoding - no Google Maps API client")
            return df
            
        # Create a copy to avoid SettingWithCopyWarning
        df_copy = df.copy()
        
        # Add coordinate columns
        df_copy['latitude'] = None
        df_copy['longitude'] = None
        
        print(f"Geocoding {len(df_copy)} unique addresses...")
        
        for idx, row in df_copy.iterrows():
            address = row['address']
            print(f"Geocoding {idx+1}/{len(df_copy)}: {address}")
            
            lat, lng = self.geocode_address(address)
            if lat and lng:
                df_copy.at[idx, 'latitude'] = lat
                df_copy.at[idx, 'longitude'] = lng
                print(f"  ✓ {lat}, {lng}")
            else:
                print("  ✗ No coordinates found")
                
            # Add delay to respect API rate limits
            time.sleep(0.1)
            
        # Count successful geocoding
        successful_geocoding = df_copy[df_copy['latitude'].notna()].shape[0]
        print(f"✓ Successfully geocoded {successful_geocoding}/{len(df_copy)} addresses")
        
        return df_copy
            
    def get_available_regions(self) -> List[str]:
        """Extract all available regions from the dropdown menu"""
        self.driver.get(self.base_url)
        time.sleep(5)  # Wait for page to load
        
        # Wait for the region dropdown to be present
        wait = WebDriverWait(self.driver, 15)
        region_dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='areano']"))
        )
        
        # Get all options from the dropdown
        select = Select(region_dropdown)
        regions = []
        
        for option in select.options:
            region_name = option.text.strip()
            if region_name and region_name != "請選擇(鄉鎮市區)":
                regions.append(region_name)
                
        print(f"Found {len(regions)} regions: {regions}")
        return regions
    
    def extract_polling_stations_for_region(self, region: str) -> List[Dict]:
        """Extract polling station data for a specific region"""
        # Navigate to the base URL
        self.driver.get(self.base_url)
        time.sleep(5)
        
        # Wait for the region dropdown and select the region
        wait = WebDriverWait(self.driver, 15)
        region_dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='areano']"))
        )
        
        # Select the region
        select = Select(region_dropdown)
        select.select_by_visible_text(region)
        print(f"Selected region: {region}")
        
        # Find and click the search button
        search_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '搜')]")
        print(f"Found search button: {search_button.text}")
        search_button.click()
        
        # Wait for the table to load completely
        time.sleep(8)  # Increased wait time
        
        # Wait for table to be present and have data
        table = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
        
        # Wait additional time for data to load
        time.sleep(5)
        
        # Check if table has data rows (more than just header)
        rows = table.find_elements(By.CSS_SELECTOR, "tr")
        if len(rows) <= 1:  # Only header row
            raise ValueError(f"Table for {region} has no data rows")
            
        print(f"Found {len(rows)-1} data rows for {region}")
        
        # Parse the table
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        table = soup.find('table')
        
        if not table:
            raise ValueError(f"No table found for region: {region}")
        
        stations = []
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:
                station_data = {
                    'region': region,
                    'number': cells[0].get_text(strip=True),
                    'location': cells[1].get_text(strip=True),
                    'address': cells[2].get_text(strip=True),
                    'village_neighborhood': cells[3].get_text(strip=True),
                    'google_maps_url': None
                }
                
                # Extract Google Maps URL from the address cell
                address_link = cells[2].find('a')
                if address_link and address_link.get('href'):
                    station_data['google_maps_url'] = address_link.get('href')
                    
                stations.append(station_data)
                
        print(f"Extracted {len(stations)} polling stations for {region}")
        return stations
    
    def parse_all_regions(self):
        """Parse polling station data for all regions"""
        self.setup_driver()
        
        # Get all available regions
        regions = self.get_available_regions()
        
        if not regions:
            raise ValueError("No regions found!")
        
        # Extract data for each region
        for i, region in enumerate(regions, 1):
            print(f"Processing region {i}/{len(regions)}: {region}")
            stations = self.extract_polling_stations_for_region(region)
            self.data.extend(stations)
            
            # Add a small delay between regions
            time.sleep(3)
            
        print(f"Total polling stations extracted: {len(self.data)}")
        self.close_driver()
    
    def validate_data_completeness(self, expected_stations_per_region: Dict[str, int]):
        """Validate that all expected polling stations were extracted"""
        df = pd.DataFrame(self.data)
        
        for region, expected_count in expected_stations_per_region.items():
            actual_count = len(df[df['region'] == region])
            if actual_count < expected_count:
                missing = expected_count - actual_count
                raise ValueError(f"Missing {missing} polling stations for {region}. Expected: {expected_count}, Got: {actual_count}")
            print(f"✓ {region}: {actual_count}/{expected_count} stations")
    
    def process_data_with_deduplication_and_geocoding(self):
        """Process the extracted data with deduplication and geocoding"""
        if not self.data:
            raise ValueError("No data to process!")
            
        # Convert to DataFrame
        df = pd.DataFrame(self.data)
        print(f"Processing {len(df)} records...")
        
        # Step 1: Identify and remove duplicates
        print("\nStep 1: Identifying duplicates...")
        unique_df, duplicate_df = self.identify_duplicates(df)
        
        # Step 2: Geocode unique addresses
        print("\nStep 2: Geocoding unique addresses...")
        unique_df_with_coords = self.geocode_unique_addresses(unique_df)
        
        # Step 3: Update the data with processed results
        self.data = unique_df_with_coords.to_dict('records')
        
        print(f"\nFinal processed data: {len(self.data)} unique records")
    
    def save_data(self):
        """Save the extracted data to CSV and JSON files"""
        if not self.data:
            raise ValueError("No data to save!")
            
        # Create DataFrame
        df = pd.DataFrame(self.data)
        
        # Save to CSV
        csv_path = "data/polling_stations_with_coordinates.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Data saved to CSV: {csv_path}")
        
        # Save to JSON
        json_path = "data/polling_stations_with_coordinates.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to JSON: {json_path}")
        
        # Print summary
        print("\nSummary:")
        print(f"Total unique polling stations: {len(self.data)}")
        print(f"Regions covered: {df['region'].nunique()}")
        print(f"Stations with Google Maps URLs: {df[df['google_maps_url'].notna()].shape[0]}")
        print(f"Stations with coordinates: {df[df['latitude'].notna()].shape[0]}")


def main():
    """Main function to run the parser"""
    parser = PollingStationParser()
    parser.parse_all_regions()
    parser.process_data_with_deduplication_and_geocoding()
    parser.save_data()


if __name__ == "__main__":
    main() 