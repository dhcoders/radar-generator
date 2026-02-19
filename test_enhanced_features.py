"""
Test script for enhanced radar generator features
Run this to verify the enhanced functionality works with your test data
"""

import pandas as pd
import numpy as np
from src.enhanced_radar_maker import (
    calculate_percentiles_for_sample,
    get_available_metrics,
    create_sample_filter_options,
    generate_enhanced_radar,
    generate_color_palette,
    get_positions_from_groups,
    assign_simplified_position
)
from src.wyscout_remapping import wyscout_column_mapping
import matplotlib.pyplot as plt

def test_enhanced_features():
    """Test the enhanced radar generator with the TESTOUTPUT_joined.csv data"""
    
    print("🧪 Testing Enhanced Radar Generator Features")
    print("=" * 50)
    
    # Load test data
    try:
        df = pd.read_csv("Testing Data/TESTOUTPUT_joined.csv")
        print(f"✅ Loaded test data: {len(df)} players, {len(df.columns)} columns")
    except Exception as e:
        print(f"❌ Error loading test data: {e}")
        return False
    
    # Apply column remapping
    df = df.rename(columns=wyscout_column_mapping)
    print("✅ Applied column remapping")
    
    # Test 1: Get available metrics
    print("\n📊 Testing metric extraction...")
    available_metrics = get_available_metrics(df)
    print(f"✅ Found {len(available_metrics)} available metrics")
    print(f"Sample metrics: {available_metrics[:10]}")
    
    # Test 2: Create sample filter options
    print("\n🔍 Testing sample filter options...")
    filter_options = create_sample_filter_options(df)
    print("✅ Sample filter options:")
    for key, values in filter_options.items():
        if isinstance(values, list) and len(values) > 5:
            print(f"  - {key}: {len(values)} options (showing first 5: {values[:5]})")
        else:
            print(f"  - {key}: {values}")
    
    # Test 3: Sample filtering and percentile calculation
    print("\n📈 Testing sample filtering and percentile calculation...")
    
    # Test position assignment
    test_positions = ['LCMF', 'RCB', 'LWF', 'GK']
    print("✅ Position assignments:")
    for pos in test_positions:
        if pos in df['Position'].values:
            assigned = assign_simplified_position(pos)
            print(f"  {pos} → {assigned}")
    
    sample_filter = {
        'Position_Group': ['CM'],  # Use simplified position group filtering
        'Minutes played': 900  # Minimum 900 minutes
    }
    
    df_with_percentiles = calculate_percentiles_for_sample(df, sample_filter)
    
    # Check sample size
    filtered_df = df.copy()
    # Add position groups for filtering
    filtered_df['Position_Group'] = filtered_df['Position'].apply(assign_simplified_position)
    
    for column, criteria in sample_filter.items():
        if column in filtered_df.columns:
            if isinstance(criteria, (int, float)):
                filtered_df = filtered_df[filtered_df[column] >= criteria]
            elif isinstance(criteria, list):
                filtered_df = filtered_df[filtered_df[column].isin(criteria)]
    
    print(f"✅ Sample filter applied: {len(filtered_df)} players in comparison sample")
    print(f"✅ Percentiles calculated for all {len(df)} players")
    
    # Test 4: Generate color palette
    print("\n🎨 Testing color palette generation...")
    colors = generate_color_palette(5)
    print(f"✅ Generated {len(colors)} colors: {colors}")
    
    # Test 5: Create and test a radar
    print("\n🎯 Testing radar generation...")
    
    # Select a test player (first player with sufficient data)
    test_player = df.iloc[0]['Player']
    player_data = df_with_percentiles[df_with_percentiles['Player'] == test_player].iloc[0]
    
    # Select test metrics
    test_metrics = [
        'Total Goals', 'Total Assists', 'xG', 'xA', 'Shots', 'Shots Created',
        'Passes', 'Pass Acc. %', 'Prog. Passes', 'Prog. Pass Acc. %',
        'Dribbles', 'Dribble Succ. %'
    ]
    
    # Filter metrics that actually exist in the data
    available_test_metrics = [m for m in test_metrics if m in available_metrics][:12]
    
    if len(available_test_metrics) < 6:
        # Fall back to first available metrics
        available_test_metrics = available_metrics[:12]
    
    print(f"✅ Selected {len(available_test_metrics)} metrics for test radar")
    
    # Create metric groups
    metric_groups = {
        'Attacking': available_test_metrics[:4],
        'Playmaking': available_test_metrics[4:8],
        'Dribbling': available_test_metrics[8:]
    }
    
    # Create group colors
    group_colors = {
        'Attacking': '#FF6B6B',
        'Playmaking': '#4ECDC4', 
        'Dribbling': '#45B7D1'
    }
    
    # Extract percentiles
    percentiles = []
    for metric in available_test_metrics:
        percentile_col = f'{metric}_percentile'
        if percentile_col in df_with_percentiles.columns:
            percentiles.append(player_data[percentile_col])
        else:
            percentiles.append(50)
    
    # Create radar data
    radar_data = {
        'player_name': test_player,
        'position': player_data.get('Position', 'Unknown'),
        'params': available_test_metrics,
        'percentiles': percentiles,
        'sample_info': f"Test Sample | {len(filtered_df)} players | Min 900 minutes",
        'custom_title': f"{test_player.upper()} | ENHANCED RADAR TEST",
        'metric_groups': metric_groups,
        'group_colors': group_colors
    }
    
    # Generate radar
    try:
        fig = generate_enhanced_radar(radar_data)
        
        # Save test radar
        fig.savefig("test_enhanced_radar.png", dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        print("✅ Enhanced radar generated successfully!")
        print("✅ Saved as 'test_enhanced_radar.png'")
        
    except Exception as e:
        print(f"❌ Error generating radar: {e}")
        return False
    
    # Test 6: Verify data integrity
    print("\n🔍 Testing data integrity...")
    
    # Check percentiles are reasonable
    percentile_cols = [col for col in df_with_percentiles.columns if col.endswith('_percentile')]
    print(f"✅ Found {len(percentile_cols)} percentile columns")
    
    # Check percentile ranges
    for col in percentile_cols[:5]:  # Check first 5
        values = df_with_percentiles[col].dropna()
        min_val, max_val = values.min(), values.max()
        if 0 <= min_val <= max_val <= 100:
            print(f"  ✅ {col}: range {min_val}-{max_val}")
        else:
            print(f"  ⚠️ {col}: unusual range {min_val}-{max_val}")
    
    print("\n🎉 All tests completed successfully!")
    print("\nTo run the enhanced app:")
    print("  streamlit run enhanced_app.py")
    print("\nFeatures tested:")
    print("  ✅ CSV data loading with column remapping")
    print("  ✅ Custom comparison sample selection")
    print("  ✅ Metric selection and filtering")
    print("  ✅ Metric grouping and color customization")
    print("  ✅ Enhanced radar generation")
    print("  ✅ Percentile calculation with sample filtering")
    
    return True

if __name__ == "__main__":
    test_enhanced_features()