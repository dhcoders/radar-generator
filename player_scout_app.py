"""
Player Scouting & Shortlisting App
Advanced filtering system to find players based on multiple criteria
"""

import pandas as pd
import numpy as np
import streamlit as st
from src.enhanced_radar_maker import (
    create_sample_filter_options,
    get_available_metrics,
    get_positions_from_groups
)
from src.wyscout_remapping import wyscout_column_mapping
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Player Scout",
    page_icon="PS",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("PLAYER SHORTLISTING TOOL")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'metric_filters' not in st.session_state:
    st.session_state.metric_filters = {}
if 'demographic_filters' not in st.session_state:
    st.session_state.demographic_filters = {}

# Auto-load the test data
if st.session_state.df is None:
    try:
        # Load the test data automatically
        df = pd.read_csv("Data/player_data_2026-02-13_113150.csv")
        
        # Apply column remapping
        df = df.rename(columns=wyscout_column_mapping)
        
        # Store in session state
        st.session_state.df = df
        
    except Exception as e:
        st.error(f"Error loading scouting data: {str(e)}")

# Main content area
if st.session_state.df is not None:
    df = st.session_state.df
    
    # Move demographic filters to sidebar
    with st.sidebar:
        st.header("Filters")
        
        # Get filter options
        filter_options = create_sample_filter_options(df)
        
        demographic_filters = {}
        
        # Position Groups
        if 'Position_Groups' in filter_options:
            position_groups = st.multiselect(
                "Position Selection:",
                options=filter_options['Position_Groups'],
                default=st.session_state.demographic_filters.get('position_groups', []),
                help="Select one or more position groups",
                key="position_groups_sidebar"
            )
            if position_groups:
                demographic_filters['position_groups'] = position_groups
        
        # Competition
        if 'Competition' in filter_options:
            with st.expander("Competition Selection", expanded=False):
                st.write("Select competitions to include:")
                
                # Initialize competitions if not in session state
                if 'selected_competitions' not in st.session_state:
                    st.session_state.selected_competitions = st.session_state.demographic_filters.get('competitions', [])
                
                selected_competitions = []
                
                # Create checkboxes for each competition
                for comp in filter_options['Competition']:
                    is_selected = comp in st.session_state.selected_competitions
                    if st.checkbox(comp, value=is_selected, key=f"comp_{comp}"):
                        selected_competitions.append(comp)
                
                # Update session state
                st.session_state.selected_competitions = selected_competitions
                
                if selected_competitions:
                    demographic_filters['competitions'] = selected_competitions
                    st.write(f"Selected: {len(selected_competitions)} competitions")
                else:
                    st.write("No competitions selected (all included)")
        
        # Age Range
        if 'Age' in filter_options:
            min_age = min(filter_options['Age'])
            max_age = max(filter_options['Age'])
            age_range = st.slider(
                "Age Range:",
                min_value=min_age,
                max_value=max_age,
                value=st.session_state.demographic_filters.get('age_range', (min_age, max_age)),
                help="Filter by player age",
                key="age_range_sidebar"
            )
            demographic_filters['age_range'] = age_range
        
        # Minutes Range
        if 'Minutes played' in df.columns:
            min_mins = int(df['Minutes played'].min())
            max_mins = int(df['Minutes played'].max())
            minutes_range = st.slider(
                "Minutes Played:",
                min_value=min_mins,
                max_value=max_mins,
                value=st.session_state.demographic_filters.get('minutes_range', (min_mins, max_mins)),
                help="Filter by total minutes played",
                key="minutes_range_sidebar"
            )
            demographic_filters['minutes_range'] = minutes_range
        
        # Update session state
        st.session_state.demographic_filters = demographic_filters
        
        # Clear all filters button
        if st.button("Clear All Filters", type="secondary", key="clear_all_filters_sidebar"):
            st.session_state.demographic_filters = {}
            st.session_state.metric_filters = {}
            st.rerun()
    
    # Main area with tabs for metric filters and results
    tab1, tab2, tab3 = st.tabs([
        "Metric Filters", 
        "Sample Exploration",
        "Shortlist Results"
    ])
    
    # Tab 1: Metric Filters
    with tab1:
        st.header("Metric Filters")
        st.write("Set specific thresholds for performance metrics to find players who meet your criteria.")
        
        # Get available metrics and current filtered sample
        available_metrics = get_available_metrics(df)
        
        # Apply current demographic filters to get the sample for metric statistics
        current_sample = df.copy()
        demographic_filters = st.session_state.demographic_filters
        
        # Apply demographic filters to current sample
        if demographic_filters.get('position_groups'):
            # Use Position_Group column directly instead of converting back to individual positions
            current_sample = current_sample[current_sample['Position_Group'].isin(demographic_filters['position_groups'])]
        
        if demographic_filters.get('competitions'):
            current_sample = current_sample[current_sample['Competition'].isin(demographic_filters['competitions'])]
        
        
        if demographic_filters.get('age_range'):
            min_age, max_age = demographic_filters['age_range']
            current_sample = current_sample[(current_sample['Age'] >= min_age) & (current_sample['Age'] <= max_age)]
        
        if demographic_filters.get('minutes_range'):
            min_mins, max_mins = demographic_filters['minutes_range']
            current_sample = current_sample[(current_sample['Minutes played'] >= min_mins) & (current_sample['Minutes played'] <= max_mins)]
        
        
        # Define metric categories (same as radar generator)
        metric_categories = {
            "Finishing": ["Goals", "xG", "Non-Pen. Goals", "Shots", "Shots on Target %", "Goal Conversion %", "xG per Shot"],
            "Creating": ["Assists", "xA", "Shots Created", "Shot assists", "Second assists", "Third assists", "xA per Shot Assist", "Key Passes"],
            "Passing": ["Passes", "Pass Acc. %", "Forward Passes", "Forward Pass Acc. %", "Long Passes", "Long Pass Acc. %", "Short / Medium Passes", "Short / Medium Pass Acc. %"],
            "Progression": ["Prog. Passes", "Prog. Pass Acc. %", "Prog. Carries", "Passes to PA", "Passes to PA Acc. %", "Carries to PA", "Carries to Final Third"],
            "Dribbling": ["Dribbles", "Dribble Succ. %", "Accelerations", "Fouls Drawn", "Touches in PA"],
            "Defending": ["Succ. Def. Actions", "Interceptions", "Shot Blocked", "Slide Tackles", "Slide Tackle Succ. %", "Fouls"],
            "Duels": ["Combined Duels", "Combined Duels Won %", "Att. Ground Duels", "Ground Duels Won %", "Att. Aerial Duels", "Aerial Duels Won %"]
        }
        
        # Metric Selection using tabbed interface (same as radar generator)
        st.subheader("Select Metrics to Filter")
        st.write("Choose which metrics you want to set filters for, then configure thresholds below.")
        
        # Create tabs for each category
        category_names = list(metric_categories.keys())
        category_tabs = st.tabs(category_names)
        
        # Initialize selected metrics for filtering if not already done
        if 'metrics_to_filter' not in st.session_state:
            st.session_state.metrics_to_filter = []
        
        # Track selected metrics across all categories
        all_selected = set(st.session_state.metrics_to_filter)
        
        for i, (category_name, category_metrics) in enumerate(metric_categories.items()):
            with category_tabs[i]:
                st.write(f"**Select {category_name} metrics to filter:**")
                
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
                                key=f"filter_metric_{category_name}_{metric}"
                            )
                            
                            # Update selection
                            if selected and metric not in all_selected:
                                all_selected.add(metric)
                            elif not selected and metric in all_selected:
                                all_selected.discard(metric)
                    
                    # Show selection count
                    selected_count = len([m for m in available_in_category if m in all_selected])
                    if selected_count > 0:
                        st.success(f"{selected_count} of {len(available_in_category)} selected for filtering")
                    else:
                        st.info(f"0 of {len(available_in_category)} selected for filtering")
                else:
                    st.info("No metrics from this category found in your data")
        
        # Update session state with all selected metrics
        st.session_state.metrics_to_filter = list(all_selected)
        
        # Configure Filters for Selected Metrics
        st.write("---")
        st.subheader("Configure Metric Filters")
        
        if st.session_state.metrics_to_filter:
            st.write(f"**Configure filters for your {len(st.session_state.metrics_to_filter)} selected metrics:**")
            
            # Create expandable sections for each selected metric
            for metric in st.session_state.metrics_to_filter:
                with st.expander(f"{metric}", expanded=metric in st.session_state.metric_filters):
                    if metric in current_sample.columns:
                        metric_data = current_sample[metric].dropna()
                        
                        if len(metric_data) > 0:
                            # Get metric bounds for input validation
                            min_val = float(metric_data.min())
                            max_val = float(metric_data.max())
                            mean_val = float(metric_data.mean())
                            
                            # Simple minimum threshold filter
                            threshold = st.number_input(
                                f"Minimum {metric}:",
                                min_value=min_val,
                                max_value=max_val,
                                value=min_val,
                                step=(max_val - min_val) / 100 if max_val > min_val else 0.001,
                                format="%.3f",
                                key=f"min_threshold_{metric}",
                                help=f"Players with {metric} above this value will be included"
                            )
                            
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                if st.button("Add/Update Filter", key=f"add_min_{metric}"):
                                    st.session_state.metric_filters[metric] = {
                                        "type": "min",
                                        "value": threshold
                                    }
                                    st.success(f"Filter set: {metric} ≥ {threshold:.3f}")
                                    st.rerun()
                            
                            with col2:
                                if metric in st.session_state.metric_filters:
                                    if st.button("Remove Filter", key=f"remove_{metric}"):
                                        del st.session_state.metric_filters[metric]
                                        st.rerun()
                            
                            # Show current filter status
                            if metric in st.session_state.metric_filters:
                                filter_config = st.session_state.metric_filters[metric]
                                st.info(f"**Active Filter:** {metric} ≥ {filter_config['value']:.3f}")
                        else:
                            st.warning(f"No data available for {metric} in current sample")
                    else:
                        st.error(f"Metric {metric} not found in dataset")
        else:
            st.info("Select metrics from the tabs above to configure filters")
        
        # Show summary of active filters
        if st.session_state.metric_filters:
            st.write("---")
            st.subheader("Active Metric Filters Summary")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{len(st.session_state.metric_filters)} active filters:**")
                for metric, filter_config in st.session_state.metric_filters.items():
                    st.write(f"• **{metric}** ≥ {filter_config['value']:.3f}")
            
            with col2:
                if st.button("Clear All Filters", type="secondary", key="clear_metric_filters"):
                    st.session_state.metric_filters = {}
                    st.rerun()
    
    # Tab 2: Sample Exploration
    with tab2:
        st.header("Sample Exploration")
        st.write("Explore data distributions and percentiles to help set informed filter thresholds.")
        
        # Apply current demographic filters to get the exploration sample
        exploration_sample = df.copy()
        demographic_filters = st.session_state.demographic_filters
        
        # Apply demographic filters to exploration sample
        if demographic_filters.get('position_groups'):
            # Use Position_Group column directly instead of converting back to individual positions
            exploration_sample = exploration_sample[exploration_sample['Position_Group'].isin(demographic_filters['position_groups'])]
        
        if demographic_filters.get('competitions'):
            exploration_sample = exploration_sample[exploration_sample['Competition'].isin(demographic_filters['competitions'])]
        
        if demographic_filters.get('age_range'):
            min_age, max_age = demographic_filters['age_range']
            exploration_sample = exploration_sample[(exploration_sample['Age'] >= min_age) & (exploration_sample['Age'] <= max_age)]
        
        if demographic_filters.get('minutes_range'):
            min_mins, max_mins = demographic_filters['minutes_range']
            exploration_sample = exploration_sample[(exploration_sample['Minutes played'] >= min_mins) & (exploration_sample['Minutes played'] <= max_mins)]
        
        # Show current sample info
        st.subheader(f"Current Sample: {len(exploration_sample)} Players")
        
        if len(exploration_sample) == 0:
            st.warning("No players match your current demographic filters. Adjust the filters in the sidebar to see data.")
        else:
            # Sample composition
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Positions:**")
                pos_counts = exploration_sample['Position_Group'].value_counts()
                for pos, count in pos_counts.items():
                    st.write(f"• {pos}: {count}")
            
            with col2:
                st.write("**Competitions:**")
                comp_counts = exploration_sample['Competition'].value_counts()
                for comp, count in comp_counts.head(5).items():
                    st.write(f"• {comp}: {count}")
                if len(comp_counts) > 5:
                    st.write(f"• ... and {len(comp_counts) - 5} more")
            
            with col3:
                st.write("**Age Distribution:**")
                st.write(f"• Min: {exploration_sample['Age'].min()}")
                st.write(f"• Max: {exploration_sample['Age'].max()}")
                st.write(f"• Average: {exploration_sample['Age'].mean():.1f}")
                st.write(f"• Median: {exploration_sample['Age'].median():.1f}")
            
            # Metric exploration
            st.write("---")
            st.subheader("Metric Percentiles & Distribution")
            
            # Get available metrics
            available_metrics = get_available_metrics(df)
            
            # Metric categories for organization
            metric_categories = {
                "Finishing": ["Goals", "xG", "Non-Pen. Goals", "Shots", "Shots on Target %", "Goal Conversion %", "xG per Shot"],
                "Creating": ["Assists", "xA", "Shots Created", "Shot assists", "Second assists", "Third assists", "xA per Shot Assist", "Key Passes"],
                "Passing": ["Passes", "Pass Acc. %", "Forward Passes", "Forward Pass Acc. %", "Long Passes", "Long Pass Acc. %", "Short / Medium Passes", "Short / Medium Pass Acc. %"],
                "Progression": ["Prog. Passes", "Prog. Pass Acc. %", "Prog. Carries", "Passes to PA", "Passes to PA Acc. %", "Carries to PA", "Carries to Final Third"],
                "Dribbling": ["Dribbles", "Dribble Succ. %", "Accelerations", "Fouls Drawn", "Touches in PA"],
                "Defending": ["Succ. Def. Actions", "Interceptions", "Shot Blocked", "Slide Tackles", "Slide Tackle Succ. %", "Fouls"],
                "Duels": ["Combined Duels", "Combined Duels Won %", "Att. Ground Duels", "Ground Duels Won %", "Att. Aerial Duels", "Aerial Duels Won %"]
            }
            
            # Select metric category
            selected_category = st.selectbox(
                "Select metric category to explore:",
                options=list(metric_categories.keys()),
                key="exploration_category"
            )
            
            # Get metrics for selected category that exist in data
            category_metrics = [m for m in metric_categories[selected_category] if m in available_metrics]
            
            if category_metrics:
                # Select specific metric
                selected_metric = st.selectbox(
                    f"Select {selected_category.lower()} metric:",
                    options=category_metrics,
                    key="exploration_metric"
                )
                
                if selected_metric in exploration_sample.columns:
                    metric_data = exploration_sample[selected_metric].dropna()
                    
                    if len(metric_data) > 0:
                        # Calculate percentiles
                        percentiles = [10, 25, 50, 75, 90, 95]
                        percentile_values = [metric_data.quantile(p/100) for p in percentiles]
                        
                        st.write(f"**{selected_metric} Distribution:**")
                        
                        # Display percentiles in columns
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Key Statistics:**")
                            st.write(f"• Min: {metric_data.min():.3f}")
                            st.write(f"• Max: {metric_data.max():.3f}")
                            st.write(f"• Mean: {metric_data.mean():.3f}")
                            st.write(f"• Std Dev: {metric_data.std():.3f}")
                            st.write(f"• Sample Size: {len(metric_data)}")
                        
                        with col2:
                            st.write("**Percentiles:**")
                            for p, val in zip(percentiles, percentile_values):
                                st.write(f"• {p}th percentile: {val:.3f}")
                        
                        # Suggested filter thresholds
                        st.write("**Suggested Filter Thresholds:**")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.info(f"**Top 25%**: ≥ {percentile_values[3]:.3f}")
                        with col2:
                            st.info(f"**Top 10%**: ≥ {percentile_values[4]:.3f}")
                        with col3:
                            st.info(f"**Top 5%**: ≥ {percentile_values[5]:.3f}")
                        
                        # Quick filter buttons
                        st.write("**Quick Add Filter:**")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button(f"Filter Top 25%", key="filter_75th"):
                                st.session_state.metric_filters[selected_metric] = {
                                    "type": "min",
                                    "value": percentile_values[3]
                                }
                                st.success(f"Added filter: {selected_metric} ≥ {percentile_values[3]:.3f}")
                                st.rerun()
                        
                        with col2:
                            if st.button(f"Filter Top 10%", key="filter_90th"):
                                st.session_state.metric_filters[selected_metric] = {
                                    "type": "min",
                                    "value": percentile_values[4]
                                }
                                st.success(f"Added filter: {selected_metric} ≥ {percentile_values[4]:.3f}")
                                st.rerun()
                        
                        with col3:
                            if st.button(f"Filter Top 5%", key="filter_95th"):
                                st.session_state.metric_filters[selected_metric] = {
                                    "type": "min",
                                    "value": percentile_values[5]
                                }
                                st.success(f"Added filter: {selected_metric} ≥ {percentile_values[5]:.3f}")
                                st.rerun()
                        
                        # Show distribution histogram
                        import plotly.express as px
                        import plotly.graph_objects as go
                        
                        fig = px.histogram(
                            x=metric_data,
                            nbins=30,
                            title=f"{selected_metric} Distribution",
                            labels={'x': selected_metric, 'y': 'Count'}
                        )
                        
                        # Add percentile lines
                        colors = ['red', 'orange', 'green', 'blue', 'purple', 'black']
                        for i, (p, val) in enumerate(zip(percentiles, percentile_values)):
                            fig.add_vline(
                                x=val,
                                line_dash="dash",
                                line_color=colors[i],
                                annotation_text=f"{p}th: {val:.2f}"
                            )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning(f"No data available for {selected_metric} in current sample")
                else:
                    st.error(f"Metric {selected_metric} not found in dataset")
            else:
                st.warning(f"No {selected_category.lower()} metrics found in the dataset")
    
    # Tab 3: Results
    with tab3:
        st.header("Scouting Results")
        
        # Apply all filters
        filtered_df = df.copy()
        
        # Apply demographic filters
        demographic_filters = st.session_state.demographic_filters
        
        # Apply position group filters
        if demographic_filters.get('position_groups'):
            # Use Position_Group column directly instead of converting back to individual positions
            filtered_df = filtered_df[filtered_df['Position_Group'].isin(demographic_filters['position_groups'])]
        
        # Apply competition filters
        if demographic_filters.get('competitions'):
            filtered_df = filtered_df[filtered_df['Competition'].isin(demographic_filters['competitions'])]
        
        # Apply age range filters
        if demographic_filters.get('age_range'):
            min_age, max_age = demographic_filters['age_range']
            filtered_df = filtered_df[(filtered_df['Age'] >= min_age) & (filtered_df['Age'] <= max_age)]
        
        # Apply minutes played filters
        if demographic_filters.get('minutes_range'):
            min_mins, max_mins = demographic_filters['minutes_range']
            filtered_df = filtered_df[(filtered_df['Minutes played'] >= min_mins) & (filtered_df['Minutes played'] <= max_mins)]
        
        # Apply metric filters
        metric_filters = st.session_state.metric_filters
        for metric, filter_config in metric_filters.items():
            if metric in filtered_df.columns:
                if filter_config["type"] == "min":
                    filtered_df = filtered_df[filtered_df[metric] >= filter_config["value"]]
                elif filter_config["type"] == "max":
                    filtered_df = filtered_df[filtered_df[metric] <= filter_config["value"]]
                elif filter_config["type"] == "range":
                    min_val, max_val = filter_config["value"]
                    filtered_df = filtered_df[
                        (filtered_df[metric] >= min_val) & 
                        (filtered_df[metric] <= max_val)
                    ]
        
        # Show results
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"Found {len(filtered_df)} Players")
            
            if len(filtered_df) > 0:
                # Select columns to display
                display_columns = ['Player', 'Position', 'Team', 'Competition', 'Age', 'Minutes played']
                
                # Add active metric filters to display
                for metric in metric_filters.keys():
                    if metric in filtered_df.columns and metric not in display_columns:
                        display_columns.append(metric)
                
                # Show the results table
                display_df = filtered_df[display_columns].copy()
                
                # Format numeric columns
                for col in display_df.columns:
                    if display_df[col].dtype in ['float64', 'int64'] and col not in ['Age', 'Minutes played']:
                        display_df[col] = display_df[col].round(3)
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400
                )
                
                # Download button
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Shortlist as CSV",
                    data=csv,
                    file_name=f"player_shortlist_{len(filtered_df)}_players.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No players match your current filter criteria. Try adjusting your filters.")
        
        with col2:
            st.subheader("Filter Summary")
            
            # Show filter breakdown
            if demographic_filters or metric_filters:
                total_filters = len(demographic_filters) + len(metric_filters)
                st.metric("Active Filters", total_filters)
                st.metric("Players Found", len(filtered_df))
                
                if len(df) > 0:
                    percentage = (len(filtered_df) / len(df)) * 100
                    st.metric("% of Database", f"{percentage:.1f}%")
                
                # Reset filters button
                if st.button("Clear All Filters", type="secondary", key="clear_all_filters"):
                    st.session_state.demographic_filters = {}
                    st.session_state.metric_filters = {}
                    st.rerun()
            else:
                st.info("No filters applied. Use the previous tabs to set up your search criteria.")
            
            # Quick stats if we have results
            if len(filtered_df) > 0:
                st.write("**Quick Stats:**")
                
                # Position breakdown
                if 'Position_Group' in filtered_df.columns:
                    pos_counts = filtered_df['Position_Group'].value_counts()
                    st.write("*Position Groups:*")
                    for pos, count in pos_counts.head(5).items():
                        st.write(f"• {pos}: {count}")
                
                # Competition breakdown
                if 'Competition' in filtered_df.columns:
                    comp_counts = filtered_df['Competition'].value_counts()
                    st.write("*Top Competitions:*")
                    for comp, count in comp_counts.head(3).items():
                        st.write(f"• {comp}: {count}")

else:
    # No data loaded yet
    st.info("👆 Loading scouting database...")
    st.rerun()

# Footer
st.markdown("---")
st.markdown("**Player Scouting Tool** - Advanced filtering system for player recruitment and analysis")