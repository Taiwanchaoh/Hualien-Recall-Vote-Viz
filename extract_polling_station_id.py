import pandas as pd
import re

# Read the voting data
voting_data = pd.read_csv('./data/recall_vote_data_detailed.csv')

# Filter out the "總計" rows
mask = voting_data["投開票所名稱"] != "總計"
voting_data = voting_data[mask]

# Function to extract polling station ID from the format "第XXX投開票所"
def extract_polling_station_id(station_name):
    # Use regex to find the number between "第" and "投開票所"
    match = re.search(r'第(\d+)投開票所', station_name)
    if match:
        return int(match.group(1))
    else:
        return None

# Apply the function to extract IDs
voting_data['polling_station_id'] = voting_data['投開票所名稱'].apply(extract_polling_station_id)

# Display the first few rows to verify the extraction
print("First 10 rows with extracted polling station IDs:")
print(voting_data[['投開票所名稱', 'polling_station_id']].head(10))

# Check for any rows where extraction failed
failed_extractions = voting_data[voting_data['polling_station_id'].isna()]
if not failed_extractions.empty:
    print(f"\nWarning: {len(failed_extractions)} rows failed to extract polling station ID:")
    print(failed_extractions['投開票所名稱'].unique())

# Save the updated data
voting_data.to_csv('./data/recall_vote_data_detailed_with_ids.csv', index=False)
print(f"\nUpdated data saved to './data/recall_vote_data_detailed_with_ids.csv'")
print(f"Total rows processed: {len(voting_data)}")
print(f"Rows with valid polling station IDs: {len(voting_data) - len(failed_extractions)}") 