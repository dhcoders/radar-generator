"""
Debug script to check position assignments
"""

import pandas as pd
from src.enhanced_radar_maker import assign_simplified_position
from src.wyscout_remapping import wyscout_column_mapping

# Load and process data
df = pd.read_csv("Testing Data/TESTOUTPUT_joined.csv")
df = df.rename(columns=wyscout_column_mapping)

# Filter to Premier League only
pl_df = df[df['Competition'] == 'ENG Premier League'].copy()
print(f"Total Premier League players: {len(pl_df)}")

# Add simplified positions
pl_df['Position_Group'] = pl_df['Position'].apply(assign_simplified_position)

# Count by position group
position_counts = pl_df['Position_Group'].value_counts()
print("\nPosition group counts in Premier League:")
for pos, count in position_counts.items():
    print(f"  {pos}: {count} players")

# Check WM assignments specifically
wm_players = pl_df[pl_df['Position_Group'] == 'WM']
print(f"\nWM players ({len(wm_players)}):")
print("Original Position -> Assigned Group")
for _, player in wm_players.iterrows():
    print(f"  {player['Player']}: {player['Position']} -> {player['Position_Group']}")

# Check what positions start with wide midfielder codes
print("\nAll positions that start with wide midfielder codes:")
wide_positions = pl_df[pl_df['Position'].str.contains(r'^(LW|RW|LWF|RWF|LAMF|RAMF)', na=False)]
print(f"Found {len(wide_positions)} players with positions starting with LW/RW/LWF/RWF/LAMF/RAMF")

for _, player in wide_positions.head(10).iterrows():
    assigned = assign_simplified_position(player['Position'])
    print(f"  {player['Player']}: {player['Position']} -> {assigned}")

# Check Summerville specifically
summerville = pl_df[pl_df['Player'] == 'C. Summerville']
if not summerville.empty:
    player = summerville.iloc[0]
    print(f"\nC. Summerville:")
    print(f"  Position: {player['Position']}")
    print(f"  Assigned: {assign_simplified_position(player['Position'])}")
    print(f"  Minutes played: {player['Minutes played']}")
else:
    print("\nC. Summerville not found in Premier League data")

# Test the filtering logic that the app would use
print(f"\nTesting sample filtering (WM + Premier League + 900+ minutes):")
sample_filter = {
    'Position_Group': ['WM'],
    'Competition': ['ENG Premier League'],
    'Minutes played': 900
}

# Apply filters step by step
filtered_df = pl_df.copy()
print(f"Starting with: {len(filtered_df)} Premier League players")

# Filter by position group
if 'Position_Group' in sample_filter:
    filtered_df = filtered_df[filtered_df['Position_Group'].isin(sample_filter['Position_Group'])]
    print(f"After WM filter: {len(filtered_df)} players")

# Filter by minutes played
if 'Minutes played' in sample_filter:
    filtered_df = filtered_df[filtered_df['Minutes played'] >= sample_filter['Minutes played']]
    print(f"After 900+ minutes filter: {len(filtered_df)} players")

print(f"\nFinal sample size: {len(filtered_df)} WM players")
print("Players in final sample:")
for _, player in filtered_df.iterrows():
    print(f"  {player['Player']}: {player['Minutes played']} minutes")