#!/usr/bin/env python3
"""
Script to check if polling stations are within geometry boundaries and append associated primary name.
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def main():
    print("Loading polling stations with coordinates...")
    # Read polling stations with coordinates
    polling_stations = pd.read_csv('data/polling_stations_with_coordinates.csv')
    print(f"Loaded {len(polling_stations)} polling stations")
    
    print("Loading hualien division area village geometry...")
    # Read the parquet file directly as a GeoDataFrame
    village_areas = gpd.read_parquet('maps/hualien_division_area_village.geoparquet')
    print(f"Loaded {len(village_areas)} village areas")
    print(f"Columns: {village_areas.columns.tolist()}")
    
    # Create GeoDataFrame for polling stations
    print("Creating GeoDataFrame for polling stations...")
    geometry = [Point(lon, lat) for lon, lat in zip(polling_stations['longitude'], polling_stations['latitude'])]
    polling_gdf = gpd.GeoDataFrame(polling_stations, geometry=geometry, crs=village_areas.crs)
    
    print("Performing spatial join...")
    # Perform spatial join to find which polling stations are within which village areas
    # 'within' predicate means polling stations must be completely within the village geometry
    joined = gpd.sjoin(polling_gdf, village_areas, how='left', predicate='within')
    
    print(f"Join results: {len(joined)} rows")
    print(f"Polling stations with matching areas: {joined['primary_name'].notna().sum()}")
    print(f"Polling stations without matching areas: {joined['primary_name'].isna().sum()}")
    
    # Select relevant columns for output
    output_columns = ['polling_station_id', 'polling_station_name', 'address', 
                     'longitude', 'latitude', 'primary_name']
    
    # Filter to only include columns that exist
    existing_columns = [col for col in output_columns if col in joined.columns]
    result_df = joined[existing_columns].copy()
    
    # Rename primary_name to area_name for clarity
    if 'primary_name' in result_df.columns:
        result_df = result_df.rename(columns={'primary_name': 'area_name'})
    
    print("Saving results...")
    result_df.to_csv('data/polling_station_area.csv', index=False)
    print("Results saved to data/polling_station_area.csv")
    
    # Show some sample results
    print("\nSample results:")
    print(result_df.head(10))
    
    # Show summary statistics
    print(f"\nSummary:")
    print(f"Total polling stations: {len(result_df)}")
    print(f"Stations with area assignment: {result_df['area_name'].notna().sum()}")
    print(f"Stations without area assignment: {result_df['area_name'].isna().sum()}")

if __name__ == "__main__":
    main() 