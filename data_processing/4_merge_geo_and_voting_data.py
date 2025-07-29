import pandas as pd
import geopandas as gpd


voting_data = pd.read_csv('./data/recall_vote_data_detailed.csv')
polling_station_data = pd.read_csv('./data/polling_stations_with_coordinates.csv')

print(voting_data.head())
# print(polling_station_data.info())

