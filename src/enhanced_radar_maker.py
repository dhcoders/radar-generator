"""
Enhanced radar chart generation with improved styling and performance
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
from mplsoccer import PyPizza
from PIL import Image
from pathlib import Path
from scipy.stats import percentileofscore
import matplotlib.patches as patches


def wrap_parameter_names(params: List[str], max_length: int = 12) -> List[str]:
    """
    Wrap long parameter names onto multiple lines to prevent overlap
    
    Args:
        params: List of parameter names
        max_length: Maximum characters per line before wrapping
        
    Returns:
        List of wrapped parameter names
    """
    wrapped_params = []
    
    for param in params:
        if len(param) <= max_length:
            wrapped_params.append(param)
        else:
            # Find good break points (spaces, periods, etc.)
            words = param.replace('.', '. ').replace('%', '% ').split()
            
            lines = []
            current_line = ""
            
            for word in words:
                # If adding this word would exceed max_length, start new line
                if current_line and len(current_line + " " + word) > max_length:
                    lines.append(current_line.strip())
                    current_line = word
                else:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
            
            # Add the last line
            if current_line:
                lines.append(current_line.strip())
            
            # Join lines with newline character
            wrapped_params.append("\n".join(lines))
    
    return wrapped_params


def generate_enhanced_radar(radar_data: Dict) -> plt.Figure:
    """
    Generate an enhanced radar chart with improved styling and performance
    
    Args:
        radar_data: Dictionary containing all radar parameters
        
    Returns:
        matplotlib Figure object
    """
    # Extract data from radar_data
    player_name = radar_data.get('player_name', 'Unknown Player')
    params = radar_data.get('params', [])
    percentiles = radar_data.get('percentiles', [])
    color_scheme = radar_data.get('color_scheme', 'performance')
    single_color = radar_data.get('single_color', '#5D688A')
    gradient_type = radar_data.get('gradient_type', 'warm_to_cool')
    position_group = radar_data.get('position_group', 'Unknown')
    team = radar_data.get('team', 'Unknown Team')
    league = radar_data.get('league', 'Unknown League')
    sample_positions = radar_data.get('sample_positions', [])
    
    # Load fonts first (needed for radar generation)
    import matplotlib.font_manager as fm
    
    try:
        # Try to load local fonts using matplotlib directly
        font_bold_prop = fm.FontProperties(fname='fonts/AlteHaasGroteskBold.ttf')
        font_regular_prop = fm.FontProperties(fname='fonts/AlteHaasGroteskRegular.ttf')
        
        # Create FontManager-like objects
        font_bold = type('FontManager', (), {'prop': font_bold_prop})()
        font_regular = type('FontManager', (), {'prop': font_regular_prop})()
    except:
        # Use system fonts directly - no network calls
        font_bold_prop = fm.FontProperties(weight='bold')
        font_regular_prop = fm.FontProperties(weight='normal')
        font_bold = type('FontManager', (), {'prop': font_bold_prop})()
        font_regular = type('FontManager', (), {'prop': font_regular_prop})()

    # Validate inputs
    if not params or not percentiles:
        raise ValueError("Parameters and percentiles are required")
    
    if len(params) != len(percentiles):
        raise ValueError(f"Parameters ({len(params)}) and percentiles ({len(percentiles)}) must have the same length")
    
    # Ensure percentiles are valid numbers
    clean_percentiles = []
    for pct in percentiles:
        try:
            clean_pct = float(pct)
            if pd.isna(clean_pct) or clean_pct < 0 or clean_pct > 100:
                clean_pct = 50.0
            clean_percentiles.append(clean_pct)
        except (ValueError, TypeError):
            clean_percentiles.append(50.0)
    
    percentiles = clean_percentiles
    
    # Generate colors for metrics based on scheme
    slice_colors, text_colors = generate_simplified_colors(params, percentiles, color_scheme, single_color, gradient_type)
    
    # Wrap long parameter names to prevent overlap
    wrapped_params = wrap_parameter_names(params, max_length=12)
    
    # Create the radar chart with cream/papery background
    baker = PyPizza(
        params=wrapped_params,
        background_color="#f5eddc",
        straight_line_color="#000000",
        straight_line_lw=0,
        last_circle_lw=1,
        last_circle_color="#ddd0b8",
        other_circle_lw=1,
        other_circle_color="#ddd0b8",  # A shade darker than background
        inner_circle_size=15
    )
    
    # Data validation complete - ready for PyPizza
    
    # Convert to numpy arrays to ensure compatibility
    import numpy as np
    percentiles_array = np.array(percentiles, dtype=float)
    
    # Generate the pizza plot with all formatting
    # Try to move values inward by using a custom approach
    fig, ax = baker.make_pizza(
        percentiles_array,
        figsize=(7, 8),
        param_location=110,  # Back to 110 as preferred
        slice_colors=slice_colors,
        value_colors=text_colors,
        value_bck_colors=slice_colors,
        blank_alpha=0.4,
        kwargs_slices=dict(edgecolor="#f5eddc", zorder=2, linewidth=7),
        kwargs_params=dict(
            color="#000000", fontsize=10,  # Params at 10
            fontproperties=font_bold.prop, va="center"
        ),
        kwargs_values=dict(
            color="#000000", fontsize=9,   # Values at 9
            fontproperties=font_bold.prop, zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="cornflowerblue",
                boxstyle="round,pad=0.2", lw=0.1  # Slightly smaller padding
            )
        )
    )
    
    # Skip PyPizza's built-in adjustment and go straight to manual approach
    # This ensures we have full control and can see debug output
    
    # Try a different approach: Adjust font sizes and padding for high percentiles
    try:
        fig.canvas.draw()
        
        # Positioning adjustments removed - accepting some overlap for now
        # The radar uses font size 8 and padding 0.1 which should minimize most overlap
        print("No position adjustments applied")
                        
    except Exception as e2:
        print(f"Font/padding adjustment failed: {e2}")
    
    # Value positioning is now handled in the manual approach above
    
    # AU logo in center of radar (behind radar data so it doesn't cover low values)
    try:
        logo_path = Path(__file__).parent / "BLACK PNG (2).png"
        
        if logo_path.exists():
            # Load the logo as PIL Image
            logo = Image.open(logo_path)
            
            # AU logo in center
            from mpl_toolkits.axes_grid1.inset_locator import inset_axes
            ax_logo = inset_axes(ax, width="19%", height="19%", loc='center', borderpad=0)
            ax_logo.imshow(logo, alpha=0.9)
            ax_logo.axis('off')
            ax_logo.zorder = -1
            
    except Exception as e:
        print(f"Logo loading failed: {e}")
    
    # Fonts already loaded at the beginning of the function
    
    # Generate position groups text for subtitle
    if len(sample_positions) == 1:
        position_groups_text = f"{sample_positions[0]}s"
    elif len(sample_positions) > 1:
        position_groups_text = ", ".join(sample_positions[:-1]) + f" & {sample_positions[-1]}s"
    else:
        position_groups_text = "All Positions"
    
    # Add title and subtitle with proper spacing
    title = f"{player_name} | {team}"
    subtitle = f"{league} 25/26 | Percentiles vs {position_groups_text}"
    
    # Position title and subtitle closer to radar
    title_y = 0.95
    sample_y = 0.92
    
    fig.text(0.5, title_y, title, size=18, ha="center", fontproperties=font_bold.prop, color="#000000")
    fig.text(0.5, sample_y, subtitle, size=14, ha="center", fontproperties=font_regular.prop, color="#000000")
    
    # Add color legend for performance colors
    if color_scheme == "performance":
        # Get gradient colors for legend
        gradient_colors = {
            'warm_to_cool': ['#e8a5a5', '#f4b5a5', '#f5d5a5', '#f5f5a5', '#b5d5a5', '#95d595'],
            'blue_scale': ['#ffcccc', '#cce6ff', '#99d6ff', '#66c2ff', '#3399ff', '#0066cc'],
            'purple_scale': ['#f0e6ff', '#e6ccff', '#d9b3ff', '#cc99ff', '#bf80ff', '#9933ff'],
            'ocean': ['#ffe6e6', '#e6f3ff', '#cce6ff', '#99d6ff', '#66b3ff', '#0080ff'],
            'sunset': ['#ffe6cc', '#ffcc99', '#ffb366', '#ff9933', '#ff6600', '#cc3300']
        }
        
        colors = gradient_colors.get(gradient_type, gradient_colors['warm_to_cool'])
        
        legend_colors = [
            (colors[5], "Top 10%"),
            (colors[4], "Top 25%"),
            (colors[3], "Top 50%"),
            (colors[2], "Bottom 50%"),
            (colors[1], "Bottom 25%"),
            (colors[0], "Bottom 10%")
        ]
        
        # Legend positioning (bottom right) - moved further right
        legend_x = 0.86
        legend_y_start = 0.10  # Moved down from 0.15
        
        # Legend title
        fig.text(legend_x, legend_y_start + 0.10, "Percentiles", 
                 size=8, ha="left", fontproperties=font_bold.prop, color="#000000", weight='bold')
        
        # Legend items with better spacing and square boxes
        for i, (color, label) in enumerate(legend_colors):
            y_pos = legend_y_start + 0.08 - (i * 0.018)  # More spacing between items
            
            # Square color box using figure coordinates
            rect = patches.Rectangle(
                (legend_x, y_pos - 0.006), 0.012, 0.012,  # Square: same width and height
                facecolor=color, edgecolor="#000000", linewidth=0.5,
                transform=fig.transFigure
            )
            fig.patches.append(rect)
            
            # Label text with more space from box
            fig.text(legend_x + 0.020, y_pos, label, size=7, ha="left", 
                     fontproperties=font_bold.prop, color="#000000", va="center")
    
    return fig


def generate_simplified_colors(params: List[str], percentiles: List[float], 
                             color_scheme: str, single_color: str, gradient_type: str = 'warm_to_cool') -> Tuple[List[str], List[str]]:
    """
    Generate colors for radar slices based on the selected scheme
    
    Args:
        params: List of parameter names
        percentiles: List of percentile values
        color_scheme: 'single' or 'performance'
        single_color: Hex color for single color scheme
        gradient_type: Type of gradient for performance scheme
        
    Returns:
        Tuple of (slice_colors, text_colors)
    """
    slice_colors = []
    text_colors = []
    
    if color_scheme == "single":
        # Single color for all slices
        for _ in percentiles:
            slice_colors.append(single_color)
            text_colors.append("#FFFFFF")  # White text on colored background
    else:
        # Define different gradient color sets
        gradient_colors = {
            'warm_to_cool': ['#e8a5a5', '#f4b5a5', '#f5d5a5', '#f5f5a5', '#b5d5a5', '#95d595'],
            'blue_scale': ['#ffcccc', '#cce6ff', '#99d6ff', '#66c2ff', '#3399ff', '#0066cc'],
            'purple_scale': ['#f0e6ff', '#e6ccff', '#d9b3ff', '#cc99ff', '#bf80ff', '#9933ff'],
            'ocean': ['#ffe6e6', '#e6f3ff', '#cce6ff', '#99d6ff', '#66b3ff', '#0080ff'],
            'sunset': ['#ffe6cc', '#ffcc99', '#ffb366', '#ff9933', '#ff6600', '#cc3300']
        }
        
        colors = gradient_colors.get(gradient_type, gradient_colors['warm_to_cool'])
        
        # Apply gradient colors based on percentiles
        for percentile in percentiles:
            # Ensure percentile is a number
            try:
                pct = float(percentile) if percentile is not None else 50.0
            except (ValueError, TypeError):
                pct = 50.0  # Default to 50th percentile if conversion fails
                
            if pct <= 10:
                slice_colors.append(colors[0])    # Very poor (0-10th percentile)
            elif pct <= 25:
                slice_colors.append(colors[1])    # Poor (11-25th percentile)
            elif pct <= 50:
                slice_colors.append(colors[2])    # Below average (26-50th percentile)
            elif pct <= 75:
                slice_colors.append(colors[3])    # Above average (51-75th percentile)
            elif pct <= 90:
                slice_colors.append(colors[4])    # Good (76-90th percentile)
            else:
                slice_colors.append(colors[5])    # Excellent (91-100th percentile)
            text_colors.append("#000000")
    
    return slice_colors, text_colors


def calculate_player_percentiles_fast(df: pd.DataFrame, player_name: str, selected_metrics: List[str], sample_filter: Optional[Dict] = None) -> List[float]:
    """
    Fast percentile calculation for a single player and specific metrics only
    
    Args:
        df: DataFrame with player data
        player_name: Name of the player to calculate percentiles for
        selected_metrics: List of metrics to calculate percentiles for
        sample_filter: Optional dictionary with filter criteria
        
    Returns:
        List of percentiles for the selected metrics
    """
    # Get player data
    player_row = df[df['Player'] == player_name].iloc[0]
    
    # Apply sample filter to get comparison sample
    filtered_df = df.copy()
    
    if sample_filter:
        # Apply position group filter
        if sample_filter.get('Position_Group'):
            filtered_df = filtered_df[filtered_df['Position_Group'].isin(sample_filter['Position_Group'])]
        
        # Apply minutes played filter
        if sample_filter.get('Minutes played'):
            filtered_df = filtered_df[filtered_df['Minutes played'] >= sample_filter['Minutes played']]
        
        # Apply competition filter
        if sample_filter.get('Competition'):
            filtered_df = filtered_df[filtered_df['Competition'].isin(sample_filter['Competition'])]
        
        # Apply age filter
        if sample_filter.get('Age'):
            age_range = sample_filter['Age']
            if isinstance(age_range, (list, tuple)) and len(age_range) == 2:
                filtered_df = filtered_df[
                    (filtered_df['Age'] >= age_range[0]) & 
                    (filtered_df['Age'] <= age_range[1])
                ]
    
    percentiles = []
    
    for metric in selected_metrics:
        if metric not in df.columns:
            percentiles.append(50.0)  # Default if metric doesn't exist
            continue
            
        player_value = player_row[metric]
        
        # Handle missing player values
        if pd.isna(player_value):
            percentiles.append(50.0)
            continue
            
        # Get sample values for this metric
        sample_values = filtered_df[metric]
        sample_values = pd.to_numeric(sample_values, errors='coerce').dropna()
        
        if len(sample_values) == 0:
            percentiles.append(50.0)
            continue
            
        # Calculate percentile
        try:
            percentile = percentileofscore(sample_values, float(player_value), kind='rank')
            percentiles.append(round(percentile, 1))
        except Exception:
            percentiles.append(50.0)
    
    return percentiles


def calculate_percentiles_for_sample(df: pd.DataFrame, sample_filter: Dict) -> pd.DataFrame:
    """
    Calculate percentiles for all players in a filtered sample
    
    Args:
        df: DataFrame with player data
        sample_filter: Dictionary with filter criteria
        
    Returns:
        DataFrame with percentile columns added
    """
    # Apply filters to get the sample
    filtered_df = df.copy()
    
    if sample_filter.get('Position_Group'):
        filtered_df = filtered_df[filtered_df['Position_Group'].isin(sample_filter['Position_Group'])]
    
    if sample_filter.get('Minutes played'):
        filtered_df = filtered_df[filtered_df['Minutes played'] >= sample_filter['Minutes played']]
    
    if sample_filter.get('Competition'):
        filtered_df = filtered_df[filtered_df['Competition'].isin(sample_filter['Competition'])]
    
    if sample_filter.get('Age'):
        age_range = sample_filter['Age']
        if isinstance(age_range, (list, tuple)) and len(age_range) == 2:
            filtered_df = filtered_df[
                (filtered_df['Age'] >= age_range[0]) & 
                (filtered_df['Age'] <= age_range[1])
            ]
    
    # Get numeric columns for percentile calculation
    numeric_columns = filtered_df.select_dtypes(include=[np.number]).columns
    exclude_columns = ['Age', 'Market value', 'Minutes played', 'Matches played', 'Height', 'Weight']
    metric_columns = [col for col in numeric_columns if col not in exclude_columns]
    
    # Calculate percentiles for each metric
    percentile_df = filtered_df.copy()
    
    for metric in metric_columns:
        if metric in filtered_df.columns:
            metric_values = pd.to_numeric(filtered_df[metric], errors='coerce')
            
            # Calculate percentiles for all players
            percentiles = []
            for value in metric_values:
                if pd.isna(value):
                    percentiles.append(np.nan)
                else:
                    clean_values = metric_values.dropna()
                    if len(clean_values) > 0:
                        pct = percentileofscore(clean_values, value, kind='rank')
                        percentiles.append(round(pct, 1))
                    else:
                        percentiles.append(50.0)
            
            percentile_df[f'{metric}_percentile'] = percentiles
    
    return percentile_df


def get_available_metrics(df: pd.DataFrame) -> List[str]:
    """
    Get list of available numeric metrics from the dataframe
    
    Args:
        df: DataFrame with player data
        
    Returns:
        List of available metric column names
    """
    # Get numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Exclude non-metric columns
    exclude_columns = [
        'Age', 'Market value', 'Minutes played', 'Matches played', 
        'Height', 'Weight', 'Contract expires', '90s'
    ]
    
    # Filter out excluded columns
    available_metrics = [col for col in numeric_columns if col not in exclude_columns]
    
    return sorted(available_metrics)


def create_sample_filter_options(df: pd.DataFrame) -> Dict:
    """
    Create filter options based on available data
    
    Args:
        df: DataFrame with player data
        
    Returns:
        Dictionary with filter options
    """
    filter_options = {}
    
    # Position groups
    if 'Position_Group' in df.columns:
        filter_options['Position_Groups'] = sorted(df['Position_Group'].dropna().unique().tolist())
    
    # Competitions
    if 'Competition' in df.columns:
        filter_options['Competition'] = sorted(df['Competition'].dropna().unique().tolist())
    
    # Minutes played range
    if 'Minutes played' in df.columns:
        min_minutes = int(df['Minutes played'].min())
        max_minutes = int(df['Minutes played'].max())
        # Create range in steps of 100
        minutes_options = list(range(min_minutes, max_minutes + 100, 100))
        filter_options['Minutes played'] = minutes_options
    
    # Age range
    if 'Age' in df.columns:
        min_age = int(df['Age'].min())
        max_age = int(df['Age'].max())
        filter_options['Age'] = (min_age, max_age)
    
    return filter_options


def display_enhanced_radar_in_streamlit(radar_data: Dict):
    """
    Generate and display the radar chart in Streamlit
    
    Args:
        radar_data: Dictionary containing radar parameters
    """
    try:
        import streamlit as st
        
        # Generate the radar
        fig = generate_enhanced_radar(radar_data)
        
        # Display in Streamlit
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)  # Close to prevent memory leaks
        
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Error generating enhanced radar: {str(e)}")
        return False


def get_positions_from_groups(position_groups: List[str]) -> List[str]:
    """
    Convert position groups to individual positions
    
    Args:
        position_groups: List of position group codes
        
    Returns:
        List of individual position names
    """
    position_mapping = {
        'GK': ['Goalkeeper'],
        'CB': ['Centre-Back'],
        'FB': ['Full-back', 'Wing-back'],
        'CM': ['Central Midfielder', 'Defensive Midfielder'],
        'WM': ['Wide Midfielder', 'Wing Midfielder'],
        'AM': ['Attacking Midfielder', 'Central Attacking Midfielder'],
        'WF': ['Winger', 'Wide Forward'],
        'CF': ['Centre-Forward', 'Striker']
    }
    
    positions = []
    for group in position_groups:
        if group in position_mapping:
            positions.extend(position_mapping[group])
    
    return positions


# Global font variables for consistent usage
import matplotlib.font_manager as fm

try:
    # Try to load local fonts using matplotlib directly
    font_bold_prop = fm.FontProperties(fname='fonts/AlteHaasGroteskBold.ttf')
    font_regular_prop = fm.FontProperties(fname='fonts/AlteHaasGroteskRegular.ttf')
    
    # Create FontManager-like objects
    font_bold = type('FontManager', (), {'prop': font_bold_prop})()
    font_regular = type('FontManager', (), {'prop': font_regular_prop})()
except:
    # Use system fonts directly - no network calls
    font_bold_prop = fm.FontProperties(weight='bold')
    font_regular_prop = fm.FontProperties(weight='normal')
    font_bold = type('FontManager', (), {'prop': font_bold_prop})()
    font_regular = type('FontManager', (), {'prop': font_regular_prop})()