"""
Check if the defined categories cover all available metrics
"""

import pandas as pd
from src.enhanced_radar_maker import get_available_metrics
from src.wyscout_remapping import wyscout_column_mapping

# Load data
df = pd.read_csv("Testing Data/TESTOUTPUT_joined.csv")
df = df.rename(columns=wyscout_column_mapping)

# Get all available metrics
available_metrics = get_available_metrics(df)
print(f"Total available metrics: {len(available_metrics)}")

# Define the updated categories from the app
metric_categories = {
    "⚽ Finishing": [
        "Goals", "Total Goals", "xG", "Total xG", "Non-Pen. Goals", "Total Non-Pen. Goals",
        "Shots", "Total Shots", "Shots on Target %", "Goal Conversion %", 
        "Headed Goals", "Total Headed Goals", "Succ. Attacking Actions"
    ],
    "🎯 Creating": [
        "Assists", "Total Assists", "xA", "Total xA", "Shots Created", 
        "Shot assists", "Second assists", "Third assists", "Smart passes", "Smart Pass Acc. %"
    ],
    "⚡ Passing": [
        "Passes", "Pass Acc. %", "Forward Passes", "Forward Pass Acc. %",
        "Back Passes", "Back Pass Acc. %", "Lateral Passes", "Lateral Pass Acc. %",
        "Shorter Passes", "Shorter Pass Acc. %", "Long Passes", "Long Pass Acc. %", 
        "Avg Pass Length (m)", "Avg Long Pass Length (m)", "Passes Received", "Long Passes Received"
    ],
    "🚀 Progression": [
        "Prog. Passes", "Prog. Pass Acc. %", "Prog. Carries", "Deep Completions",
        "Passes to F3", "Pass to F3 Acc. %", "Passes to PA", "Passes to PA Acc. %", 
        "Through Balls", "Through Ball Acc. %", "Touches in PA"
    ],
    "🏃 Dribbling": [
        "Dribbles", "Dribble Succ. %", "Accelerations", "Fouls Drawn"
    ],
    "✋ Defending": [
        "Succ. Def. Actions", "Interceptions", "Shot Blocked", "Slide Tackles", "PAdj Sliding Tackles"
    ],
    "💪 Duels": [
        "Combined Duels", "Combined Duels Won %", "Att. Ground Duels", "Ground Duels Won %",
        "Att. Aerial Duels", "Aerial Duels Won %", "Offensive Duels", "Offensive Duels Won %"
    ],
    "⚡ Crossing": [
        "Crosses", "Cross Acc. %", "Left Flank Crosses", "Left Flank Cross Acc. %",
        "Right Flank Crosses", "Right Flank Cross Acc. %", "Crosses to PA", "Deep Crosses"
    ],
    "⚠️ Discipline": [
        "Fouls", "Yellow cards", "Total Yellow cards", "Red cards", "Total Red cards"
    ],
    "🥅 Goalkeeping": [
        "Save %", "Clean Sheets", "Conceded Goals", "Total Conceded goals", 
        "xG Faced", "Total xG Faced", "Shots Faced", "Total Shots Faced",
        "Prevented Goals", "Total Prevented Goals", "Exits", "Rec. Back Passes", "Aerial duels per 90 (GK)"
    ],
    "⚽ Set Pieces": [
        "Free kicks per 90", "Direct free kicks per 90", "Direct free kicks on target, %",
        "Corners per 90", "Penalties taken", "Penalty conversion, %"
    ]
}

# Collect all categorized metrics
categorized_metrics = set()
for category, metrics in metric_categories.items():
    categorized_metrics.update(metrics)

print(f"Metrics in categories: {len(categorized_metrics)}")

# Find metrics that exist in data but aren't categorized
uncategorized_metrics = []
for metric in available_metrics:
    if metric not in categorized_metrics:
        uncategorized_metrics.append(metric)

print(f"\nUncategorized metrics: {len(uncategorized_metrics)}")
if uncategorized_metrics:
    print("Metrics not in any category:")
    for metric in sorted(uncategorized_metrics):
        print(f"  - {metric}")

# Find categorized metrics that don't exist in data
missing_metrics = []
for metric in categorized_metrics:
    if metric not in available_metrics:
        missing_metrics.append(metric)

print(f"\nMissing metrics (in categories but not in data): {len(missing_metrics)}")
if missing_metrics:
    print("Categorized metrics not found in data:")
    for metric in sorted(missing_metrics):
        print(f"  - {metric}")

# Show coverage by category
print(f"\nCoverage by category:")
for category, metrics in metric_categories.items():
    available_in_category = [m for m in metrics if m in available_metrics]
    coverage = len(available_in_category) / len(metrics) * 100 if metrics else 0
    category_clean = category.split(' ', 1)[1]  # Remove emoji
    print(f"  {category_clean}: {len(available_in_category)}/{len(metrics)} ({coverage:.1f}%)")

# Show sample of available metrics for context
print(f"\nSample of all available metrics (first 20):")
for i, metric in enumerate(sorted(available_metrics)[:20]):
    print(f"  {i+1:2d}. {metric}")

if len(available_metrics) > 20:
    print(f"  ... and {len(available_metrics) - 20} more")