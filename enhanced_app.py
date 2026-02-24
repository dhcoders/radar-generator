"""
Enhanced Streamlit app for radar chart generation
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
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

# Page configuration
st.set_page_config(
    page_title="Enhanced Radar Generator",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚽ Analytics United Player Radar Generator")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'sample_filter' not in st.session_state:
    st.session_state.sample_filter = {}
if 'selected_metrics' not in st.session_state:
    st.session_state.selected_metrics = []
if 'color_scheme' not in st.session_state:
    st.session_state.color_scheme = 'performance'
if 'single_color' not in st.session_state:
    st.session_state.single_color = '#5D688A'
if 'gradient_type' not in st.session_state:
    st.session_state.gradient_type = 'warm_to_cool'

# Load data
with st.sidebar:
    st.header("🔧 Data & Filters")
    
    # Load data automatically
    if st.session_state.df is None:
        try:
            df = pd.read_csv("Data/joined_player_data_2026-02-19_121630.csv")
            # No remapping needed - data comes with correct column names
            st.session_state.df = df
            st.success("✅ Player data loaded successfully.")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.stop()
    else:
        df = st.session_state.df
    
    # Create filter options
    filter_options = create_sample_filter_options(df)
    
    st.subheader("🎯 Define Comparison Sample")
    
    # Sample filters
    sample_filter = {}
    
    # Position Groups filter
    if 'Position_Groups' in filter_options:
        position_groups = st.multiselect(
            "Position Groups:",
            options=filter_options['Position_Groups'],
            help="Select position groups for comparison sample"
        )
        if position_groups:
            sample_filter['Position_Group'] = position_groups
    
    # Competition filter
    if 'Competition' in filter_options:
        competitions = st.multiselect(
            "Competitions:",
            options=filter_options['Competition'],
            help="Select leagues/competitions for comparison"
        )
        if competitions:
            sample_filter['Competition'] = competitions
    
    # Minutes played filter
    if 'Minutes played' in filter_options:
        min_minutes_value = int(df['Minutes played'].min())
        max_minutes_value = int(df['Minutes played'].max())
        
        min_minutes = st.slider(
            "Minimum minutes played:",
            min_value=min_minutes_value,
            max_value=max_minutes_value,
            value=min_minutes_value,
            step=10,
            help="Minimum minutes played to be included in comparison sample"
        )
        if min_minutes > min_minutes_value:
            sample_filter['Minutes played'] = min_minutes
    
    # Age filter
    if 'Age' in filter_options:
        age_min, age_max = filter_options['Age']
        age_range = st.slider(
            "Age range:",
            min_value=age_min,
            max_value=age_max,
            value=(age_min, age_max),
            help="Age range for comparison sample"
        )
        if age_range != (age_min, age_max):
            sample_filter['Age'] = age_range
    
    # Reset filters button
    if st.button("🔄 Reset All Filters", key="reset_filters"):
        st.session_state.sample_filter = {}
        st.rerun()
    
    st.session_state.sample_filter = sample_filter

# Main content
tab1, tab2, tab3 = st.tabs(["👤 Player Selection", "Metrics", "🎨 Generate Radar"])

with tab1:
    st.header("👤 Select Player")
    
    if 'Player' in df.columns:
        # Create unique player identifiers
        df['Player_Team_ID'] = df['Player'] + ' - ' + df['Team within selected timeframe']
        player_options = sorted(df['Player_Team_ID'].dropna().unique())
        
        selected_player_team = st.selectbox(
            "Search and select a player:",
            options=player_options,
            help="Type to search for a player name. Format: Player Name - Team"
        )
        
        if selected_player_team:
            selected_player = selected_player_team.split(' - ')[0]
            selected_team = selected_player_team.split(' - ')[1]
            
            player_matches = df[(df['Player'] == selected_player) & 
                              (df['Team within selected timeframe'] == selected_team)]
            if len(player_matches) > 0:
                player_data = player_matches.iloc[0]
                st.success(f"Selected: **{selected_player_team}**")
                
                # Show player info
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**League:** {player_data.get('Competition', 'N/A')}")
                    st.write(f"**Position:** {player_data.get('Position_Group', 'N/A')}")
                with col2:
                    st.write(f"**Age:** {player_data.get('Age', 'N/A')}")
                    st.write(f"**Minutes:** {player_data.get('Minutes played', 'N/A'):,}")
            else:
                st.error(f"Player not found")

with tab2:
    st.header("📊 Select Metrics")
    
    # Position presets
    position_presets = {
        "CF (Center Forward)": [
            "Accelerations", "Offensive Duels", "Prog. Carries",
            "Att. Aerial Duels", "Aerial Duels Won %", "Fouls Drawn", "Long Passes Received",
            "Passes Received", "Shorter Pass Acc. %", "Dribble Succ. %",
            "Succ. Def. Actions", "Att. Ground Duels",
            "NPxG", "Goals", "Shots"
        ]
    }
    
    st.subheader("Position Presets")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_preset = st.selectbox(
            "Choose a position preset:",
            options=["None"] + list(position_presets.keys()),
            help="Select a preset to automatically choose relevant metrics"
        )
    
    with col2:
        if st.button("Apply Preset", key="apply_preset", disabled=(selected_preset == "None")):
            if selected_preset in position_presets:
                available_metrics = get_available_metrics(df)
                preset_metrics = [m for m in position_presets[selected_preset] if m in available_metrics]
                st.session_state.selected_metrics = preset_metrics
                st.success(f"✅ Applied {selected_preset} preset ({len(preset_metrics)} metrics)")
                st.rerun()
    
    with col3:
        if st.button("Clear All", key="clear_all"):
            st.session_state.selected_metrics = []
            st.success("✅ Cleared all selections")
            st.rerun()
    
    st.divider()
    
    # Define metric categories - using exact column names from dataset  
    metric_categories = {
        "Finishing": ["Goals", "Total Goals", "xG", "Total xG", "NPxG", "Total NPxG", "NPxG per Shot", "Non-Pen. Goals", "Total Non-Pen. Goals", "Shots", "Total Shots", "Shots on Target %", "Goal Conversion %", "Headed Goals", "Total Headed Goals", "Penalty xG", "Succ. Attacking Actions"],
        "Creating": ["Assists", "Total Assists", "xA", "Total xA", "Shots Created", "Shot assists", "Second assists", "Third assists", "Smart passes", "Smart Pass Acc. %"],
        "Passing": ["Passes", "Pass Acc. %", "Forward Passes", "Forward Pass Acc. %", "Back Passes", "Back Pass Acc. %", "Lateral Passes", "Lateral Pass Acc. %", "Shorter Passes", "Shorter Pass Acc. %", "Long Passes", "Long Pass Acc. %", "Avg Pass Length (m)", "Avg Long Pass Length (m)", "Passes Received", "Long Passes Received"],
        "Progression": ["Prog. Passes", "Prog. Pass Acc. %", "Prog. Carries", "Deep Completions", "Passes to F3", "Pass to F3 Acc. %", "Passes to PA", "Passes to PA Acc. %", "Through Balls", "Through Ball Acc. %", "Touches in PA", "EFx Prog. Pass"],
        "Dribbling": ["Dribbles", "Dribble Succ. %", "Accelerations", "Fouls Drawn"],
        "Defending": ["Succ. Def. Actions", "Interceptions", "PAdj Interceptions", "Shot Blocked", "Slide Tackles", "PAdj Sliding Tackles"],
        "Duels": ["Combined Duels", "Combined Duels Won %", "Att. Ground Duels", "Ground Duels Won %", "Att. Aerial Duels", "Aerial Duels Won %", "Offensive Duels", "Offensive Duels Won %"],
        "Crossing": ["Crosses", "Cross Acc. %", "Left Flank Crosses", "Left Flank Cross Acc. %", "Right Flank Crosses", "Right Flank Cross Acc. %", "Crosses to PA", "Deep Crosses"],
        "Discipline": ["Fouls", "Yellow cards", "Total Yellow cards", "Red cards", "Total Red cards"],
        "Goalkeeping": ["Save %", "Clean Sheets", "Conceded Goals", "Total Conceded goals", "xG Faced", "Total xG Faced", "Shots Faced", "Total Shots Faced", "Prevented Goals", "Total Prevented Goals", "Exits", "Rec. Back Passes", "GK Aerial Duels"],
        "Set Pieces": ["Free kicks per 90", "Direct free kicks per 90", "Direct free kicks on target, %", "Corners per 90", "Penalties taken", "Penalty conversion, %"]
    }
    
    available_metrics = get_available_metrics(df)
    category_names = list(metric_categories.keys())
    
    # Create tabs for each metric category
    category_tabs = st.tabs(category_names)
    
    # Track selected metrics across all categories
    if 'selected_metrics' not in st.session_state:
        st.session_state.selected_metrics = []
    
    for i, (category_name, category_metrics) in enumerate(metric_categories.items()):
        with category_tabs[i]:
            # Filter to metrics that exist in data
            available_in_category = [m for m in category_metrics if m in available_metrics]
            
            if available_in_category:
                # Calculate number of columns based on metrics count
                num_metrics = len(available_in_category)
                num_cols = min(4, max(2, num_metrics // 3))  # 2-4 columns
                cols = st.columns(num_cols)
                
                st.write(f"**{category_name}** ({len(available_in_category)} metrics available)")
                
                # Create checkboxes for each metric in this category
                for idx, metric in enumerate(available_in_category):
                    col_idx = idx % num_cols
                    with cols[col_idx]:
                        # Check if metric is currently selected
                        is_selected = metric in st.session_state.selected_metrics
                        
                        # Create checkbox
                        selected = st.checkbox(
                            metric,
                            value=is_selected,
                            key=f"metric_{category_name}_{metric}"
                        )
                        
                        # Update session state
                        if selected and metric not in st.session_state.selected_metrics:
                            st.session_state.selected_metrics.append(metric)
                        elif not selected and metric in st.session_state.selected_metrics:
                            st.session_state.selected_metrics.remove(metric)
                
                # Show category summary
                selected_in_category = [m for m in available_in_category if m in st.session_state.selected_metrics]
                if selected_in_category:
                    st.success(f"✅ {len(selected_in_category)} metrics selected from {category_name}")
            else:
                st.info("No metrics from this category found in your data")
    
    # Summary
    st.divider()
    st.write(f"**Total Selected: {len(st.session_state.selected_metrics)} metrics**")
    
    if len(st.session_state.selected_metrics) < 6:
        st.warning("⚠️ Select at least 6 metrics for a meaningful radar")
    elif len(st.session_state.selected_metrics) > 12:
        st.warning("⚠️ Consider selecting fewer metrics (6-12) for better readability")

with tab3:
    st.header("🎨 Generate Radar")
    
    # Color scheme selection
    col1, col2 = st.columns(2)
    
    with col1:
        color_scheme = st.radio(
            "Color scheme:",
            options=["Performance Colors", "Single Color"],
            help="Performance Colors: Based on percentiles\nSingle Color: All slices the same color"
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
            gradient_type = st.selectbox(
                "Choose color gradient:",
                options=["Warm to Cool", "Blue Scale", "Purple Scale", "Ocean", "Sunset"],
                help="Different color gradients for performance visualization"
            )
            st.session_state.single_color = "#5D688A"
            st.session_state.color_scheme = "performance"
            st.session_state.gradient_type = gradient_type.lower().replace(" ", "_")
    
    with col2:
        # Color preview
        st.write("**Color Preview:**")
        if st.session_state.get('color_scheme') == 'single':
            color = st.session_state.get('single_color', '#5D688A')
            st.markdown(f'<div style="background-color: {color}; padding: 15px; margin: 10px 0; border-radius: 10px; color: white; text-align: center;"><b>All metrics will use this color</b></div>', unsafe_allow_html=True)
        else:
            gradient_type = st.session_state.get('gradient_type', 'warm_to_cool')
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
    
    st.divider()
    
    # Radar Configuration Summary
    if ('selected_player_team' in locals() and selected_player_team and st.session_state.selected_metrics):
        st.subheader("📋 Radar Configuration")
        
        # Get sample info for summary
        sample_positions = st.session_state.sample_filter.get('Position_Group', ['All Positions'])
        sample_competitions = st.session_state.sample_filter.get('Competition', ['All Leagues'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Player:** {selected_player_team}")
            st.write(f"**Metrics:** {len(st.session_state.selected_metrics)} selected")
            
        with col2:
            st.write(f"**Sample Positions:** {', '.join(sample_positions) if sample_positions else 'All Positions'}")
            st.write(f"**Sample Leagues:** {', '.join(sample_competitions) if sample_competitions else 'All Leagues'}")
        
        # Group metrics by category for display
        if st.session_state.selected_metrics:
            st.write("**Selected Metrics by Category:**")
            
            # Define metric categories for grouping (matching the selection categories)
            category_groups = {
                "Finishing": ["Goals", "Total Goals", "xG", "Total xG", "NPxG", "Total NPxG", "NPxG per Shot", "Non-Pen. Goals", "Total Non-Pen. Goals", "Shots", "Total Shots", "Shots on Target %", "Goal Conversion %", "Headed Goals", "Total Headed Goals", "Penalty xG", "Succ. Attacking Actions"],
                "Creating": ["Assists", "Total Assists", "xA", "Total xA", "Shots Created", "Shot assists", "Second assists", "Third assists", "Smart passes", "Smart Pass Acc. %"],
                "Passing": ["Passes", "Pass Acc. %", "Forward Passes", "Forward Pass Acc. %", "Back Passes", "Back Pass Acc. %", "Lateral Passes", "Lateral Pass Acc. %", "Shorter Passes", "Shorter Pass Acc. %", "Long Passes", "Long Pass Acc. %", "Avg Pass Length (m)", "Avg Long Pass Length (m)", "Passes Received", "Long Passes Received"],
                "Progression": ["Prog. Passes", "Prog. Pass Acc. %", "Prog. Carries", "Deep Completions", "Passes to F3", "Pass to F3 Acc. %", "Passes to PA", "Passes to PA Acc. %", "Through Balls", "Through Ball Acc. %", "Touches in PA", "EFx Prog. Pass"],
                "Dribbling": ["Dribbles", "Dribble Succ. %", "Accelerations", "Fouls Drawn"],
                "Defending": ["Succ. Def. Actions", "Interceptions", "PAdj Interceptions", "Shot Blocked", "Slide Tackles", "PAdj Sliding Tackles"],
                "Duels": ["Combined Duels", "Combined Duels Won %", "Att. Ground Duels", "Ground Duels Won %", "Att. Aerial Duels", "Aerial Duels Won %", "Offensive Duels", "Offensive Duels Won %"],
                "Crossing": ["Crosses", "Cross Acc. %", "Left Flank Crosses", "Left Flank Cross Acc. %", "Right Flank Crosses", "Right Flank Cross Acc. %", "Crosses to PA", "Deep Crosses"],
                "Discipline": ["Fouls", "Yellow cards", "Total Yellow cards", "Red cards", "Total Red cards"],
                "Goalkeeping": ["Save %", "Clean Sheets", "Conceded Goals", "Total Conceded goals", "xG Faced", "Total xG Faced", "Shots Faced", "Total Shots Faced", "Prevented Goals", "Total Prevented Goals", "Exits", "Rec. Back Passes", "GK Aerial Duels"],
                "Set Pieces": ["Free kicks per 90", "Direct free kicks per 90", "Direct free kicks on target, %", "Corners per 90", "Penalties taken", "Penalty conversion, %"]
            }
            
            # Group selected metrics by category
            for group_name, group_metrics in category_groups.items():
                selected_in_group = [m for m in st.session_state.selected_metrics if m in group_metrics]
                if selected_in_group:
                    st.write(f"• **{group_name}:** {', '.join(selected_in_group)}")
        
        st.divider()
    
    # Generate radar
    if ('selected_player_team' in locals() and selected_player_team and 
        st.session_state.selected_metrics and len(st.session_state.selected_metrics) >= 6):
        
        # Center the generate button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            generate_clicked = st.button("🎯 Generate Radar", key="generate_radar", type="primary", use_container_width=True)
        
        # Handle radar generation outside the column constraint
        if generate_clicked:
            with st.spinner("Generating radar..."):
                try:
                    # Calculate percentiles
                    percentiles = calculate_player_percentiles_fast(
                        df, selected_player, st.session_state.selected_metrics, st.session_state.sample_filter
                    )
                    
                    # Prepare radar data
                    sample_positions = st.session_state.sample_filter.get('Position_Group', [player_data.get('Position_Group', 'All Positions')])
                    
                    radar_data = {
                        'player_name': selected_player,
                        'position': player_data.get('Position', 'Unknown'),
                        'position_group': player_data.get('Position_Group', 'Unknown'),
                        'team': player_data.get('Team within selected timeframe', 'Unknown Team'),
                        'league': player_data.get('Competition', 'Unknown League'),
                        'sample_positions': sample_positions,
                        'params': st.session_state.selected_metrics,
                        'percentiles': percentiles,
                        'color_scheme': st.session_state.color_scheme,
                        'single_color': st.session_state.single_color,
                        'gradient_type': st.session_state.get('gradient_type', 'warm_to_cool')
                    }
                    
                    # Generate and display radar with size constraint
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        success = display_enhanced_radar_in_streamlit(radar_data)
                    
                    if success:
                        st.success("✅ Radar generated successfully!")
                        
                        # Center the download button
                        col1, col2, col3 = st.columns([2, 1, 2])
                        with col2:
                            try:
                                # Generate figure for download
                                fig = generate_enhanced_radar(radar_data)
                                
                                import io
                                img_buffer = io.BytesIO()
                                fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', 
                                           facecolor='#f5eddc', edgecolor='none')
                                img_buffer.seek(0)
                                
                                safe_player_name = selected_player.replace(' ', '_').replace('.', '').replace(',', '')
                                filename = f"{safe_player_name}_radar.png"
                                
                                st.download_button(
                                    label="💾 Download Radar",
                                    data=img_buffer.getvalue(),
                                    file_name=filename,
                                    mime="image/png",
                                    key="download_radar_btn",
                                    help="Download radar as high-quality PNG"
                                )
                                
                                plt.close(fig)
                                
                            except Exception as e:
                                st.error(f"❌ Error preparing download: {str(e)}")
                    
                except Exception as e:
                    st.error(f"❌ Error generating radar: {str(e)}")
    else:
        st.warning("⚠️ Complete the following to generate your radar:")
        if 'selected_player_team' not in locals() or not selected_player_team:
            st.write("❌ Select a player in the 'Player Selection' tab")
        if not st.session_state.selected_metrics:
            st.write("❌ Select metrics in the 'Metrics & Grouping' tab")
        elif len(st.session_state.selected_metrics) < 6:
            st.write(f"❌ Select at least 6 metrics (currently {len(st.session_state.selected_metrics)})")