from urllib.request import urlopen
import pandas as pd
import numpy as np
from scipy import stats
import math
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
from mplsoccer import PyPizza, add_image, FontManager
import streamlit as st
from src.enhanced_radar_maker import (
    generate_enhanced_radar, 
    calculate_percentiles_for_sample,
    calculate_player_percentiles_fast,
    get_available_metrics,
    create_sample_filter_options,
    display_enhanced_radar_in_streamlit,
    get_positions_from_groups
)
from src.wyscout_remapping import wyscout_column_mapping
from typing import Dict, List, Optional
import json

# Page configuration
st.set_page_config(
    page_title="Enhanced Radar Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("ANALYTICS UNITED RADAR GENERATOR")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'selected_metrics' not in st.session_state:
    st.session_state.selected_metrics = []
if 'color_scheme' not in st.session_state:
    st.session_state.color_scheme = "performance"
if 'single_color' not in st.session_state:
    st.session_state.single_color = "#5D688A"
if 'sample_filter' not in st.session_state:
    st.session_state.sample_filter = {}

# Force reload data if it's from old source
if st.session_state.df is not None and len(st.session_state.df.columns) == 116:
    st.session_state.df = None  # Clear old data to force reload

# Sidebar for main controls
with st.sidebar:
    
    # Auto-load the test data
    if st.session_state.df is None:
        try:
            # Load the test data automatically
            df = pd.read_csv("Data/joined_player_data_2026-02-19_121630.csv")
            
            # Apply column remapping
            df = df.rename(columns=wyscout_column_mapping)
            
            # Store in session state
            st.session_state.df = df
            
            st.success("✅ Player data loaded successfully.")
            
        except Exception as e:
            st.error(f"Error loading test data{str(e)}")
    
    # Show data info if loaded
    if st.session_state.df is not None:
        df = st.session_state.df
        
        # Add reset filters button
        if st.button("🗑️ Reset All Filters"):
            st.session_state.sample_filter = {}
            st.session_state.selected_metrics = []
            st.session_state.color_scheme = "performance"
            st.session_state.single_color = "#5D688A"
            st.rerun()
            
        st.markdown("---")
        
        # Move comparison sample controls to sidebar
        st.subheader("Define Comparison Sample")
        
        # Get filter options
        filter_options = create_sample_filter_options(df)
        
        sample_filter = {}
        
        # Position filter with simplified groups
        if 'Position_Groups' in filter_options:
            position_groups = st.multiselect(
                "Position Groups:",
                options=filter_options['Position_Groups'],
                default=[],  # No default selection
                help="Select position groups for comparison sample",
                key="sidebar_position_groups_select"
            )
            
            if position_groups:
                sample_filter['Position_Group'] = position_groups
        
        # Competition filter
        if 'Competition' in filter_options:
            competitions = st.multiselect(
                "Competitions:",
                options=filter_options['Competition'],
                default=[],  # No default selection
                key="sidebar_competitions_select"
            )
            if competitions:
                sample_filter['Competition'] = competitions
        
        # Minutes played filter (slider)
        if 'Minutes played' in filter_options:
            min_minutes_value = int(df['Minutes played'].min())
            max_minutes_value = int(df['Minutes played'].max())
            
            min_minutes = st.slider(
                "Minimum minutes played:",
                min_value=min_minutes_value,
                max_value=max_minutes_value,
                value=min_minutes_value,  # Start at minimum
                step=10,
                help="Minimum minutes to include in comparison sample"
            )
            if min_minutes > min_minutes_value:
                sample_filter['Minutes played'] = min_minutes
        
        # Age filter (slider)
        if 'Age' in filter_options:
            min_age = int(df['Age'].min())
            max_age = int(df['Age'].max())
            
            age_range = st.slider(
                "Age range:",
                min_value=min_age,
                max_value=max_age,
                value=(min_age, max_age),  # Start with full range
                help="Age range for comparison sample"
            )
            # Only add filter if not the full range
            if age_range != (min_age, max_age):
                sample_filter['Age'] = list(range(age_range[0], age_range[1] + 1))
        
        # Store sample filter in session state
        st.session_state.sample_filter = sample_filter

# Main content area
if st.session_state.df is not None:
    df = st.session_state.df
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs([
        "Player Selection", 
        "Metrics", 
        "Generate Radar"
    ])
    
    # Tab 1: Player Selection
    with tab1:
        st.header("Player Selection")
        
        # Player Selection Section
        st.subheader("Select Target Player")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if 'Player' in df.columns:
                # Create unique player identifiers with team
                df['Player_Team_ID'] = df['Player'] + ' - ' + df['Team within selected timeframe']
                player_options = sorted(df['Player_Team_ID'].dropna().unique())
                
                selected_player_team = st.selectbox(
                    "Search and select a player:",
                    options=player_options,
                    help="Type to search for a player name. Format: Player Name - Team"
                )
                
                if selected_player_team:
                    # Extract player name and team for precise lookup
                    selected_player = selected_player_team.split(' - ')[0]
                    selected_team = selected_player_team.split(' - ')[1]
                    
                    # Get the exact record matching both player and team
                    player_matches = df[(df['Player'] == selected_player) & 
                                      (df['Team within selected timeframe'] == selected_team)]
                    if len(player_matches) > 0:
                        player_data = player_matches.iloc[0]
                    else:
                        st.error(f"Player '{selected_player}' at '{selected_team}' not found in data")
                        player_data = None
                    
                    if player_data is not None:
                        # Show player info
                        st.success(f"Selected: **{selected_player_team}**")
                        
            else:
                st.error("❌ No 'Player' column found in the data")
                selected_player = None
        
        with col2:
            if selected_player and 'player_data' in locals() and player_data is not None:
                # Display key player information
                info_cols = ['Team', 'Position', 'Age', 'Competition', 'Minutes played', 'Matches played']
                available_info = {col: player_data.get(col, 'N/A') for col in info_cols if col in df.columns}
                
                if available_info:
                    st.write("**Player Information:**")
                    for key, value in available_info.items():
                        st.write(f"- **{key}:** {value}")
        
        # Player selection complete - comparison sample configured in sidebar
    
    # Tab 2: Metrics & Grouping
    with tab2:
        st.header("Select Metrics by Category")
        st.write("NOTE: Data is per 90 adjusted unless prefixed with 'Total'")
        # Get available metrics
        available_metrics = get_available_metrics(df)
        
        # Define metric categories (updated to match actual data columns)
        metric_categories = {
            "Finishing": [
                "NPxG","Goals", "Total Goals","Total xG",
                "xG", "Non-Pen. Goals", "Total Non-Pen. Goals","Total NPxG",
                "NPxG per Shot", "Total Shots", "Shots on Target %", "Goal Conversion %", 
                "Shots", "Headed Goals", "Total Headed Goals", "Succ. Attacking Actions"
            ],
            "Creating": [
                "xA", "Assists", "Total Assists", "Total xA", 
                "Shots Created", "Shot assists", "Second assists", "Third assists", "Smart passes", 
                "Smart Pass Acc. %"
            ],
            "Passing": [
                "Passes", "Pass Acc. %", "Forward Passes", "Forward Pass Acc. %",
                "Back Passes", "Back Pass Acc. %", "Lateral Passes", "Lateral Pass Acc. %",
                "Shorter Passes", "Shorter Pass Acc. %", "Long Passes", "Long Pass Acc. %", 
                "Avg Pass Length (m)", "Avg Long Pass Length (m)", "Passes Received", "Long Passes Received"
            ],
            "Progression": [
                "Prog. Passes", "Prog. Pass Acc. %", "Prog. Carries", "Deep Completions",
                "Passes to F3", "Pass to F3 Acc. %", "Passes to PA", "Passes to PA Acc. %", 
                "Through Balls", "Through Ball Acc. %", "Touches in PA", "EFx Prog. Pass"
            ],
            "Dribbling": [
                "Dribbles", "Dribble Succ. %", "Accelerations", "Fouls Drawn"
            ],
            "Defending": [
                "Succ. Def. Actions", "Interceptions", "PAdj Interceptions", "Shot Blocked", "Slide Tackles", "PAdj Sliding Tackles"
            ],
            "Duels": [
                "Combined Duels", "Combined Duels Won %", "Att. Ground Duels", "Ground Duels Won %",
                "Att. Aerial Duels", "Aerial Duels Won %", "Offensive Duels", "Offensive Duels Won %"
            ],
            "Crossing": [
                "Crosses", "Cross Acc. %", "Left Flank Crosses", "Left Flank Cross Acc. %",
                "Right Flank Crosses", "Right Flank Cross Acc. %", "Crosses to PA", "Deep Crosses"
            ],
            "Discipline": [
                "Fouls", "Yellow cards", "Total Yellow cards", "Red cards", "Total Red cards"
            ],
            "Goalkeeping": [
                "Save %", "Clean Sheets", "Conceded Goals", "Total Conceded goals", 
                "xG Faced", "Total xG Faced", "Shots Faced", "Total Shots Faced",
                "Prevented Goals", "Total Prevented Goals", "Exits", "Rec. Back Passes", "Aerial duels per 90 (GK)", "GK Aerial Duels"
            ],
            "Set Pieces": [
                "Free kicks per 90", "Direct free kicks per 90", "Direct free kicks on target, %",
                "Corners per 90", "Penalties taken", "Penalty conversion, %", "Penalty xG"
            ]

        }
        
        # Position-based metric presets
        position_presets = {
            "CF (Center Forward)": [
                "Offensive Duels", "Prog. Carries",  # Outlet
                "Att. Aerial Duels", "Aerial Duels Won %", "Fouls Drawn", "Long Passes Received",  # Hold-up
                "Passes Received", "Shorter Pass Acc. %", "Dribble Succ. %",  # Link-up
                "Att. Ground Duels",  # Pressing
                "NPxG", "Goals", "Shots"  # Goalscoring + Shots
            ]
        }
        
        # Preset selection section
        st.subheader("Position Presets")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected_preset = st.selectbox(
                "Choose a position preset:",
                options=["None"] + list(position_presets.keys()),
                help="Select a preset to automatically choose relevant metrics for the position"
            )
        
        with col2:
            if st.button("Apply Preset", key="apply_preset_btn", disabled=(selected_preset == "None")):
                if selected_preset in position_presets:
                    # Filter preset metrics to only include those available in data
                    preset_metrics = [m for m in position_presets[selected_preset] if m in available_metrics]
                    st.session_state.selected_metrics = preset_metrics
                    st.success(f"✅ Applied {selected_preset} preset ({len(preset_metrics)} metrics)")
                    st.rerun()
        
        with col3:
            if st.button("Clear All", key="clear_all_metrics_btn"):
                st.session_state.selected_metrics = []
                st.success("✅ Cleared all selections")
                st.rerun()

        
        # Create tabs for each category
        category_names = list(metric_categories.keys())
        category_tabs = st.tabs(category_names)
        
        # Initialize selected metrics if not already done
        if 'selected_metrics' not in st.session_state:
            st.session_state.selected_metrics = []
        
        # Track selected metrics across all categories
        all_selected = set(st.session_state.selected_metrics)
        
        for i, (category_name, category_metrics) in enumerate(metric_categories.items()):
            with category_tabs[i]:
                st.write(f"**Select {category_name} metrics:**")
                
                # Filter to only show metrics that exist in the data
                available_in_category = [m for m in category_metrics if m in available_metrics]
                
                if available_in_category:
                    # Determine number of columns based on number of metrics
                    num_metrics = len(available_in_category)
                    if num_metrics <= 4:
                        cols = st.columns(2)  # 2 columns for small categories
                    elif num_metrics <= 8:
                        cols = st.columns(3)  # 3 columns for medium categories  
                    else:
                        cols = st.columns(4)  # 4 columns for large categories
                    
                    # Distribute metrics across columns
                    for idx, metric in enumerate(available_in_category):
                        col_idx = idx % len(cols)
                        
                        with cols[col_idx]:
                            is_selected = metric in all_selected
                            
                            # Create checkbox
                            selected = st.checkbox(
                                metric,
                                value=is_selected,
                                key=f"metric_{category_name}_{metric}"
                            )
                            
                            # Update selection
                            if selected and metric not in all_selected:
                                all_selected.add(metric)
                            elif not selected and metric in all_selected:
                                all_selected.discard(metric)
                    
                    # Show selection count
                    selected_count = len([m for m in available_in_category if m in all_selected])
                    if selected_count > 0:
                        st.success(f"✅ {selected_count} of {len(available_in_category)} selected")
                    else:
                        st.info(f"⚪ 0 of {len(available_in_category)} selected")
                else:
                    st.info("No metrics from this category found in your data")
        
        # Update session state with all selected metrics
        st.session_state.selected_metrics = list(all_selected)
        
        # Show summary
        st.write("---")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.session_state.selected_metrics:
                st.write(f"**📊 Total Selected: {len(st.session_state.selected_metrics)} metrics**")
                
                if len(st.session_state.selected_metrics) < 6:
                    st.warning("⚠️ Select at least 6 metrics for a meaningful radar")
                elif len(st.session_state.selected_metrics) > 20:
                    st.warning("⚠️ Too many metrics may make the radar cluttered")
                else:
                    st.success("✅ Good number of metrics selected")
            else:
                st.info("No metrics selected yet")
        
        with col2:
            # Quick action buttons
            if st.button("Clear All"):
                st.session_state.selected_metrics = []
                st.rerun()
        
        # Show selected metrics
        if st.session_state.selected_metrics:
            with st.expander("📋 View Selected Metrics"):
                # Group by category for display
                for category_name, category_metrics in metric_categories.items():
                    selected_in_category = [m for m in category_metrics if m in st.session_state.selected_metrics]
                    if selected_in_category:
                        st.write(f"**{category_name}:** {', '.join(selected_in_category)}")
                
                # Reorder metrics
                st.write("**Reorder metrics:**")
                metric_order = st.text_area(
                    "Metric order (one per line):",
                    value="\n".join(st.session_state.selected_metrics),
                    help="Rearrange metrics by reordering the lines"
                )
                
                if st.button("🔄 Apply Order"):
                    new_order = [m.strip() for m in metric_order.split('\n') if m.strip()]
                    # Validate that all selected metrics are included
                    if set(new_order) == set(st.session_state.selected_metrics):
                        st.session_state.selected_metrics = new_order
                        st.success("✅ Metric order updated!")
                    else:
                        st.error("❌ Order must include all selected metrics")
    
    # Tab 3: Colors & Styling
    # Tab 3: Generate Radar (with styling options)
    with tab3:
        st.header("Generate Your Radar")
        
        # Styling Section
        if not st.session_state.selected_metrics:
            st.info("👈 Select metrics in the previous tab first")
        else:
            st.subheader("Styling Options")
            col1, col2 = st.columns(2)
            
            with col1:
                color_scheme = st.radio(
                    "Choose color scheme:",
                    options=["Performance Colors", "Single Color"],
                    help="Performance Colors: Red (poor) → Yellow (average) → Green (excellent)\nSingle Color: All slices the same color"
                )
                
                if color_scheme == "Single Color":
                    single_color = st.color_picker(
                        "Choose radar color:",
                        value="#5D688A",
                        help="All radar slices will use this color"
                    )
                    st.session_state.single_color = single_color
                    st.session_state.color_scheme = "single"
                    st.session_state.gradient_type = "default"
                else:
                    # Performance colors with gradient options
                    gradient_type = st.selectbox(
                        "Choose color gradient:",
                        options=["Warm to Cool", "Blue Scale", "Purple Scale", "Ocean", "Sunset"],
                        help="Different color gradients for performance visualization"
                    )
                    st.session_state.single_color = "#5D688A"  # Default
                    st.session_state.color_scheme = "performance"
                    st.session_state.gradient_type = gradient_type.lower().replace(" ", "_")
            
            with col2:
                # Preview
                st.write("**Color Preview:**")
                if st.session_state.get('color_scheme') == 'single':
                    color = st.session_state.get('single_color', '#5D688A')
                    st.markdown(f'<div style="background-color: {color}; padding: 15px; margin: 10px 0; border-radius: 10px; color: white; text-align: center;"><b>All metrics will use this color</b></div>', unsafe_allow_html=True)
                else:
                    # Show preview based on selected gradient
                    gradient_type = st.session_state.get('gradient_type', 'warm_to_cool')
                    
                    # Define different gradient color sets
                    gradient_colors = {
                        'warm_to_cool': ['#e8a5a5', '#f4b5a5', '#f5d5a5', '#f5f5a5', '#b5d5a5', '#95d595'],
                        'blue_scale': ['#ffcccc', '#cce6ff', '#99d6ff', '#66c2ff', '#3399ff', '#0066cc'],
                        'purple_scale': ['#f0e6ff', '#e6ccff', '#d9b3ff', '#cc99ff', '#bf80ff', '#9933ff'],
                        'ocean': ['#ffe6e6', '#e6f3ff', '#cce6ff', '#99d6ff', '#66b3ff', '#0080ff'],
                        'sunset': ['#ffe6cc', '#ffcc99', '#ffb366', '#ff9933', '#ff6600', '#cc3300']
                    }
                    
                    colors = gradient_colors.get(gradient_type, gradient_colors['warm_to_cool'])
                    
                    gradient_html = '<div style="display: flex; gap: 2px; margin: 10px 0;">'
                    labels = ['Very Poor<br>0-10%', 'Poor<br>11-25%', 'Below Avg<br>26-50%', 'Above Avg<br>51-75%', 'Good<br>76-90%', 'Excellent<br>91-100%']
                    
                    for i, (color, label) in enumerate(zip(colors, labels)):
                        gradient_html += f'<div style="background-color: {color}; padding: 8px; border-radius: 3px; color: #444; text-align: center; flex: 1; font-size: 10px;"><small>{label}</small></div>'
                    
                    gradient_html += '</div>'
                    st.markdown(gradient_html, unsafe_allow_html=True)
            
            st.markdown("---")
        
        # Radar Configuration Summary
        st.subheader("Radar Configuration")
        
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            # Player Information
            if 'selected_player_team' in locals() and selected_player_team:
                st.write("**Selected Player:**")
                st.info(f"📊 {selected_player_team}")
                
                if 'player_data' in locals() and player_data is not None:
                    st.write(f"**League:** {player_data.get('Competition', 'N/A')}")
                    st.write(f"**Position:** {player_data.get('Position_Group', 'N/A')}")
            else:
                st.warning("⚠️ No player selected")
            
            # Sample Filter Information
            st.write("**Comparison Sample:**")
            sample_filter = st.session_state.get('sample_filter', {})
            if sample_filter:
                # Calculate sample size
                filtered_df = df.copy()
                for column, criteria in sample_filter.items():
                    if column in filtered_df.columns:
                        if isinstance(criteria, (int, float)):
                            filtered_df = filtered_df[filtered_df[column] >= criteria]
                        elif isinstance(criteria, str):
                            filtered_df = filtered_df[filtered_df[column] == criteria]
                        elif isinstance(criteria, list):
                            filtered_df = filtered_df[filtered_df[column].isin(criteria)]
                
                st.write(f"**Sample Size:** {len(filtered_df):,} players")
                
                # Show filter details
                if 'Position_Group' in sample_filter:
                    positions = ", ".join(sample_filter['Position_Group'])
                    st.write(f"**Position Groups:** {positions}")
                
                if 'Competition' in sample_filter:
                    leagues = sample_filter['Competition']
                    if len(leagues) <= 3:
                        league_text = ", ".join(leagues)
                    else:
                        league_text = f"{len(leagues)} leagues selected"
                    st.write(f"**Leagues:** {league_text}")
                
                if 'Minutes played' in sample_filter:
                    st.write(f"**Min. Minutes:** {sample_filter['Minutes played']:,}")
                
                if 'Age' in sample_filter:
                    ages = sample_filter['Age']
                    st.write(f"**Age Range:** {min(ages)}-{max(ages)} years")
            else:
                st.write("📈 Full dataset (no filters)")
                st.write(f"**Sample Size:** {len(df):,} players")
        
        with config_col2:
            # Metrics Information
            st.write("**Selected Metrics:**")
            if st.session_state.selected_metrics:
                st.success(f"✅ {len(st.session_state.selected_metrics)} metrics selected")
                
                # Group metrics by category for display
                from src.enhanced_radar_maker import get_available_metrics
                available_metrics = get_available_metrics(df)
                
                # Define metric categories (same as in metrics tab)
                metric_categories = {
                    "Finishing": ["NPxG","Goals", "Total Goals","Total xG", "xG", "Non-Pen. Goals", "Total Non-Pen. Goals","Total NPxG", "NPxG per Shot", "Total Shots", "Shots on Target %", "Goal Conversion %", "Shots", "Headed Goals", "Total Headed Goals", "Succ. Attacking Actions"],
                    "Creating": ["xA", "Assists", "Total Assists", "Total xA", "Shots Created", "Shot assists", "Second assists", "Third assists", "Smart passes", "Smart Pass Acc. %"],
                    "Passing": ["Passes", "Pass Acc. %", "Forward Passes", "Forward Pass Acc. %", "Back Passes", "Back Pass Acc. %", "Lateral Passes", "Lateral Pass Acc. %", "Shorter Passes", "Shorter Pass Acc. %", "Long Passes", "Long Pass Acc. %", "Avg Pass Length (m)", "Avg Long Pass Length (m)", "Passes Received", "Long Passes Received"],
                    "Progression": ["Prog. Passes", "Prog. Pass Acc. %", "Prog. Carries", "Deep Completions", "Passes to F3", "Pass to F3 Acc. %", "Passes to PA", "Passes to PA Acc. %", "Through Balls", "Through Ball Acc. %", "Touches in PA", "EFx Prog. Pass"],
                    "Dribbling": ["Dribbles", "Dribble Succ. %", "Accelerations", "Fouls Drawn"],
                    "Defending": ["Succ. Def. Actions", "Interceptions", "PAdj Interceptions", "Shot Blocked", "Slide Tackles", "PAdj Sliding Tackles"],
                    "Duels": ["Combined Duels", "Combined Duels Won %", "Att. Ground Duels", "Ground Duels Won %", "Att. Aerial Duels", "Aerial Duels Won %", "Offensive Duels", "Offensive Duels Won %"],
                    "Crossing": ["Crosses", "Cross Acc. %", "Left Flank Crosses", "Left Flank Cross Acc. %", "Right Flank Crosses", "Right Flank Cross Acc. %", "Crosses to PA", "Deep Crosses"],
                    "Discipline": ["Fouls", "Yellow cards", "Total Yellow cards", "Red cards", "Total Red cards"],
                    "Goalkeeping": ["Save %", "Clean Sheets", "Conceded Goals", "Total Conceded goals", "xG Faced", "Total xG Faced", "Shots Faced", "Total Shots Faced", "Prevented Goals", "Total Prevented Goals", "Exits", "Rec. Back Passes", "Aerial duels per 90 (GK)", "GK Aerial Duels"],
                    "Set Pieces": ["Free kicks per 90", "Direct free kicks per 90", "Direct free kicks on target, %", "Corners per 90", "Penalties taken", "Penalty conversion, %", "Penalty xG"],
                    "General": ["90s"]
                }
                
                # Show metrics by category
                for category_name, category_metrics in metric_categories.items():
                    selected_in_category = [m for m in st.session_state.selected_metrics if m in category_metrics]
                    if selected_in_category:
                        st.write(f"**{category_name}:** {len(selected_in_category)} metrics")
            else:
                st.warning("⚠️ No metrics selected")
        
        st.markdown("---")
        
        # Check if all required data is available
        ready_to_generate = (
            'selected_player' in locals() and 
            selected_player and 
            st.session_state.selected_metrics and 
            len(st.session_state.selected_metrics) >= 6
        )
        
        if ready_to_generate:
            # Centralized generate button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Generate Radar", type="primary", use_container_width=True):
                    with st.spinner("Generating radar..."):
                        try:
                            # Fast percentile calculation - only for selected metrics and player
                            with st.spinner("Calculating percentiles..."):
                                percentiles = calculate_player_percentiles_fast(
                                    df, selected_player, st.session_state.selected_metrics, st.session_state.sample_filter
                                )
                            
                            # Get player data from original dataframe
                            player_data = df[df['Player'] == selected_player].iloc[0]
                            
                            # Group metrics by category for natural radar ordering
                            metric_categories = {
                                "Finishing": ["NPxG","Goals", "Total Goals","Total xG", "xG", "Non-Pen. Goals", "Total Non-Pen. Goals","Total NPxG", "NPxG per Shot", "Total Shots", "Shots on Target %", "Goal Conversion %", "Shots", "Headed Goals", "Total Headed Goals", "Succ. Attacking Actions"],
                                "Creating": ["xA", "Assists", "Total Assists", "Total xA", "Shots Created", "Shot assists", "Second assists", "Third assists", "Smart passes", "Smart Pass Acc. %"],
                                "Passing": ["Passes", "Pass Acc. %", "Forward Passes", "Forward Pass Acc. %", "Back Passes", "Back Pass Acc. %", "Lateral Passes", "Lateral Pass Acc. %", "Shorter Passes", "Shorter Pass Acc. %", "Long Passes", "Long Pass Acc. %", "Avg Pass Length (m)", "Avg Long Pass Length (m)", "Passes Received", "Long Passes Received"],
                                "Progression": ["Prog. Passes", "Prog. Pass Acc. %", "Prog. Carries", "Deep Completions", "Passes to F3", "Pass to F3 Acc. %", "Passes to PA", "Passes to PA Acc. %", "Through Balls", "Through Ball Acc. %", "Touches in PA", "EFx Prog. Pass"],
                                "Dribbling": ["Dribbles", "Dribble Succ. %", "Accelerations", "Fouls Drawn"],
                                "Defending": ["Succ. Def. Actions", "Interceptions", "PAdj Interceptions", "Shot Blocked", "Slide Tackles", "PAdj Sliding Tackles"],
                                "Duels": ["Combined Duels", "Combined Duels Won %", "Att. Ground Duels", "Ground Duels Won %", "Att. Aerial Duels", "Aerial Duels Won %", "Offensive Duels", "Offensive Duels Won %"],
                                "Crossing": ["Crosses", "Cross Acc. %", "Left Flank Crosses", "Left Flank Cross Acc. %", "Right Flank Crosses", "Right Flank Cross Acc. %", "Crosses to PA", "Deep Crosses"],
                                "Discipline": ["Fouls", "Yellow cards", "Total Yellow cards", "Red cards", "Total Red cards"],
                                "Goalkeeping": ["Save %", "Clean Sheets", "Conceded Goals", "Total Conceded goals", "xG Faced", "Total xG Faced", "Shots Faced", "Total Shots Faced", "Prevented Goals", "Total Prevented Goals", "Exits", "Rec. Back Passes", "Aerial duels per 90 (GK)", "GK Aerial Duels"],
                                "Set Pieces": ["Free kicks per 90", "Direct free kicks per 90", "Direct free kicks on target, %", "Corners per 90", "Penalties taken", "Penalty conversion, %", "Penalty xG"],
                                "General": ["90s"]
                            }
                            
                            # Order metrics by category for natural grouping on radar
                            ordered_metrics = []
                            ordered_percentiles = []
                            
                            # Create mapping of metric to percentile
                            metric_to_percentile = dict(zip(st.session_state.selected_metrics, percentiles))
                            
                            # Group metrics by category in order
                            for category_name, category_metrics in metric_categories.items():
                                category_selected = [m for m in category_metrics if m in st.session_state.selected_metrics]
                                for metric in category_selected:
                                    ordered_metrics.append(metric)
                                    ordered_percentiles.append(float(metric_to_percentile[metric]))
                            
                            # Ensure all data is in correct format
                            clean_params = ordered_metrics
                            clean_percentiles = ordered_percentiles
                            
                            # Prepare radar data
                            # Get sample position groups for subtitle
                            sample_positions = st.session_state.sample_filter.get('Position_Group', [player_data.get('Position_Group', 'All Positions')])
                            
                            radar_data = {
                                'player_name': selected_player,
                                'position': player_data.get('Position', 'Unknown'),
                                'position_group': player_data.get('Position_Group', player_data.get('Position', 'Unknown')),
                                'team': player_data.get('Team within selected timeframe', 'Unknown Team'),
                                'league': player_data.get('Competition', 'Unknown League'),
                                'sample_positions': sample_positions,
                                'params': clean_params,
                                'percentiles': clean_percentiles,
                                'color_scheme': st.session_state.color_scheme,
                                'single_color': st.session_state.single_color,
                                'gradient_type': st.session_state.get('gradient_type', 'warm_to_cool')
                            }
                            
                            # Generate and display radar
                            success = display_enhanced_radar_in_streamlit(radar_data)
                            
                            if success:
                                st.success("✅ Radar generated successfully!")
                                
                                # Add download button - simplified approach
                                col1, col2, col3 = st.columns([1, 1, 1])
                                with col2:
                                    try:
                                        # Generate the radar figure for download
                                        fig = generate_enhanced_radar(radar_data)
                                        
                                        # Save as PNG with matching background
                                        import io
                                        img_buffer = io.BytesIO()
                                        fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', 
                                                   facecolor='#f5eddc', edgecolor='none')  # Match radar background
                                        img_buffer.seek(0)
                                        
                                        # Create filename
                                        safe_player_name = selected_player.replace(' ', '_').replace('.', '').replace(',', '')
                                        filename = f"{safe_player_name}_radar.png"
                                        
                                        # Direct download button
                                        st.download_button(
                                            label="💾 Download Radar",
                                            data=img_buffer.getvalue(),
                                            file_name=filename,
                                            mime="image/png",
                                            key="download_radar_btn",
                                            help="Download radar as high-quality PNG"
                                        )
                                        
                                        plt.close(fig)  # Clean up
                                        
                                    except Exception as e:
                                        st.error(f"❌ Error preparing download: {str(e)}")
                                        import traceback
                                        st.code(traceback.format_exc())
                                
                                # Show metric values
                                with st.expander("📊 View Metric Values"):
                                    for i, metric in enumerate(st.session_state.selected_metrics):
                                        actual_value = player_data.get(metric, 'N/A')
                                        percentile = percentiles[i]
                                        st.write(f"**{metric}:** {actual_value} (P{percentile})")
                            
                        except Exception as e:
                            st.error(f"❌ Error generating radar: {str(e)}")
                            st.write("Please check your data and selections.")
                            
                            # More detailed error info
                            import traceback
                            st.write("**Full error details:**")
                            st.code(traceback.format_exc())
        
        else:
            # Show what's missing
            st.warning("⚠️ Complete the following to generate your radar:")
            
            if 'selected_player' not in locals() or not selected_player:
                st.write("❌ Select a player in the 'Player Selection' tab")
            
            if not st.session_state.selected_metrics:
                st.write("❌ Select metrics in the 'Metrics & Grouping' tab")
            elif len(st.session_state.selected_metrics) < 6:
                st.write(f"❌ Select at least 6 metrics (currently {len(st.session_state.selected_metrics)})")

else:
    # No data loaded yet
    st.info("🔄 Loading test data automatically...")
    st.rerun()  # This will trigger the auto-load in the sidebar

# Footer
st.markdown("---")
st.markdown("**Analytics United Radar Generator**")