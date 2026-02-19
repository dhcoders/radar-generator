"""
Test the exact filtering logic used in the enhanced app
"""

import pandas as pd
from src.enhanced_radar_maker import assign_simplified_position, calculate_percentiles_for_sample
from src.wyscout_remapping import wyscout_column_mapping

# Load and process data exactly like the app does
print("Loading data...")
df = pd.read_csv("Testing Data/TESTOUTPUT_joined.csv")
df = df.rename(columns=wyscout_column_mapping)
print(f"Loaded {len(df)} total players")

# Test the exact scenario: WM + Premier League
print("\n" + "="*50)
print("TESTING: WM + Premier League (like in the app)")
print("="*50)

# Sample filter like the app would create
sample_filter = {
    'Position_Group': ['WM'],
    'Competition': ['ENG Premier League']
}

print("Sample filter:", sample_filter)

# Apply the same filtering logic as calculate_percentiles_for_sample
df_with_positions = df.copy()
if 'Position' in df_with_positions.columns:
    df_with_positions['Position_Group'] = df_with_positions['Position'].apply(assign_simplified_position)

print(f"Added Position_Group column")

# Apply sample filter step by step (same logic as in calculate_percentiles_for_sample)
filtered_df = df_with_positions.copy()
print(f"Starting with: {len(filtered_df)} players")

for column, criteria in sample_filter.items():
    if column in filtered_df.columns:
        before_count = len(filtered_df)
        if isinstance(criteria, (int, float)):
            filtered_df = filtered_df[filtered_df[column] >= criteria]
            print(f"After {column} >= {criteria}: {len(filtered_df)} players (removed {before_count - len(filtered_df)})")
        elif isinstance(criteria, str):
            filtered_df = filtered_df[filtered_df[column] == criteria]
            print(f"After {column} == '{criteria}': {len(filtered_df)} players (removed {before_count - len(filtered_df)})")
        elif isinstance(criteria, list):
            filtered_df = filtered_df[filtered_df[column].isin(criteria)]
            print(f"After {column} in {criteria}: {len(filtered_df)} players (removed {before_count - len(filtered_df)})")

print(f"\nFinal filtered sample: {len(filtered_df)} players")

# Check if Summerville is in the filtered sample
summerville_in_sample = filtered_df[filtered_df['Player'] == 'C. Summerville']
if not summerville_in_sample.empty:
    player = summerville_in_sample.iloc[0]
    print(f"\n[YES] C. Summerville IS in the sample:")
    print(f"  Position: {player['Position']}")
    print(f"  Position_Group: {player['Position_Group']}")
    print(f"  Competition: {player['Competition']}")
    print(f"  Minutes: {player['Minutes played']}")
else:
    print(f"\n[NO] C. Summerville is NOT in the sample")

# Show some sample players
print(f"\nFirst 10 players in filtered sample:")
for _, player in filtered_df.head(10).iterrows():
    print(f"  {player['Player']}: {player['Position']} -> {player['Position_Group']} ({player['Minutes played']} min)")

# Test with minutes filter too
print(f"\n" + "="*50)
print("TESTING: WM + Premier League + 450+ minutes")
print("="*50)

sample_filter_with_minutes = {
    'Position_Group': ['WM'],
    'Competition': ['ENG Premier League'],
    'Minutes played': 450
}

filtered_df_with_minutes = df_with_positions.copy()
print(f"Starting with: {len(filtered_df_with_minutes)} players")

for column, criteria in sample_filter_with_minutes.items():
    if column in filtered_df_with_minutes.columns:
        before_count = len(filtered_df_with_minutes)
        if isinstance(criteria, (int, float)):
            filtered_df_with_minutes = filtered_df_with_minutes[filtered_df_with_minutes[column] >= criteria]
            print(f"After {column} >= {criteria}: {len(filtered_df_with_minutes)} players (removed {before_count - len(filtered_df_with_minutes)})")
        elif isinstance(criteria, str):
            filtered_df_with_minutes = filtered_df_with_minutes[filtered_df_with_minutes[column] == criteria]
            print(f"After {column} == '{criteria}': {len(filtered_df_with_minutes)} players (removed {before_count - len(filtered_df_with_minutes)})")
        elif isinstance(criteria, list):
            filtered_df_with_minutes = filtered_df_with_minutes[filtered_df_with_minutes[column].isin(criteria)]
            print(f"After {column} in {criteria}: {len(filtered_df_with_minutes)} players (removed {before_count - len(filtered_df_with_minutes)})")

print(f"\nFinal sample with minutes filter: {len(filtered_df_with_minutes)} players")