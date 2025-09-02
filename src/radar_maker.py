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

def generate_radar(radar_data):
    """
    Generate a radar chart from the extracted player data
    
    Args:
        radar_data (dict): Dictionary containing player data from session state
        
    Returns:
        matplotlib.figure.Figure: The generated radar chart figure
    """
    
    # Load custom fonts
    font_normal = FontManager('https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Regular.ttf?raw=true')
    font_bold = FontManager('https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Bold.ttf?raw=true')
    
    # Try to load local Alte Haas Grotesk fonts
    try:
        font_path_regular = Path(__file__).parent.parent / "fonts" / "AlteHaasGroteskRegular.ttf"
        font_path_bold = Path(__file__).parent.parent / "fonts" / "AlteHaasGroteskBold.ttf"
        
        if font_path_regular.exists() and font_path_bold.exists():
            font_normal = FontManager(str(font_path_regular))
            font_bold = FontManager(str(font_path_bold))
    except Exception as e:
        print(f"Could not load custom fonts, using defaults: {e}")
    
    # Extract data from the radar_data dictionary
    player_name = radar_data['player_name']
    position = radar_data['position']
    params = radar_data['params']
    percentiles = radar_data['percentiles']
    sample_info = radar_data.get('sample_info', None)
    
    # Position-specific color schemes based on metric groupings
    if position == 'CB':
        # CB: 3 groups of 4 metrics each
        # Group 1: Defensive Actions (4 metrics)
        # Group 2: Duels (4 metrics)  
        # Group 3: Progressive Play (4 metrics)
        slice_colors = (
            ["#5D688A"] * 4 +  # Red for defensive actions
            ["#F7A5A5"] * 4 +  # Blue for duels
            ["#FFDBB6"] * 4    # Green for progressive play
        )
        text_colors = (
            ["#FFFFFF"] * 4 +
            ["#000000"] * 8   # Black text on green
        )
    else:
        # All other positions: 4 groups of 3 metrics each
        # Group 1: Attacking/Finishing (3 metrics)
        # Group 2: Creativity/Playmaking (3 metrics)
        # Group 3: Progression/Mobility (3 metrics) 
        # Group 4: Defensive/Duels (3 metrics)
        slice_colors = (
            ["#5D688A"] * 3 +  # Light red for attacking
            ["#F7A5A5"] * 3 +  # Yellow for creativity
            ["#FFDBB6"] * 3 +  # Green for progression
            ["#6B2C91"] * 3    # Blue for defensive
        )
        text_colors = (
            ["#FFFFFF"] * 3 +
            ["#000000"] * 6 +
            ["#FFFFFF"] * 3
        )
    
    # Create the radar chart
    baker = PyPizza(
        params=params,
        background_color="#FFFFFF",
        straight_line_color="#000000",
        straight_line_lw=2,
        last_circle_lw=4,
        other_circle_lw=1,
        other_circle_color="#E0E0E0",
        inner_circle_size=13,
    )
    
    # Generate the pizza plot - moved down to make space for title/categories
    fig, ax = baker.make_pizza(
        percentiles,  # Use percentiles for radar visualization
        figsize=(8, 8.5),  # Slightly taller figure to accommodate text
        slice_colors=slice_colors,
        value_colors=text_colors,
        value_bck_colors=slice_colors,
        blank_alpha=0.8,
        param_location=112,
        kwargs_slices=dict(
            edgecolor="#000000", zorder=2, linewidth= 2
        ),
        kwargs_params=dict(
            color="#000000", fontsize=13,
            va="center", fontproperties=font_bold.prop
        ),
        kwargs_values=dict(
            color="#000000", fontsize=12,
            zorder=3, fontproperties=font_bold.prop,
            bbox=dict(
                edgecolor="#000000", facecolor="cornflowerblue",
                boxstyle="round,pad=0.2", lw=1
            )
        )
    )
    
    # Move the radar plot down to make space for text
    ax.set_position([0.1, 0.05, 0.8, 0.75])  # [left, bottom, width, height] - moved radar down
    
    # Add the AU logo to the center of the radar
    try:
        logo_path = Path(__file__).parent / "AULogo.png"
        
        if logo_path.exists():
            # Load the logo as PIL Image
            logo_image = Image.open(logo_path)
            
            # Add the logo to the center of the radar (adjusted for moved radar position)
            add_image(
                logo_image, fig, left=0.46525, bottom=0.39, width=0.07, height=0.07,
                alpha=1
            )
            
    except Exception as e:
        # Show error for debugging
        try:
            import streamlit as st
            st.error(f"Logo loading error: {e}")
        except:
            print(f"Error loading logo: {e}")
    
    # Add title and subtitle with position-specific context (now with more space above radar)
    title_y = 0.95
    sample_y = 0.915
    categories_y = 0.88
    
    # Main title
    fig.text(
        0.5, title_y, f"{player_name.upper()} | {position} TEMPLATE", size=25,
        color="#000000", ha="center", va="center", fontproperties=font_bold.prop
    )
    
    # Sample info (if provided)
    if sample_info:
        fig.text(
            0.5, sample_y, sample_info, size=16,
            color="#000000", ha="center", va="center", fontproperties=font_bold.prop
        )
        # Adjust categories position down if sample info is present
        categories_y = 0.88
    
    # Position-specific subtitle with color-coded categories (horizontal layout)
    if position == 'CB':
        # CB has 3 groups of 4 metrics each with different colors
        categories = ["DEFENDING", "DUELLING", "BALL-PLAYING"]
        colors = ["#5D688A", "#F7A5A5", "#FFDBB6"]
        
        # Calculate evenly spaced positions for 3 categories
        total_width = 0.4  # Reduced width for tighter spacing
        start_x = 0.5 - (total_width / 2)  # Start position (centered)
        spacing = total_width / (len(categories) - 1) if len(categories) > 1 else 0
        
        for i, (category, color) in enumerate(zip(categories, colors)):
            x_pos = start_x + (i * spacing)
            fig.text(x_pos, categories_y, category, size=14, color=color, 
                    ha="center", va="center", fontproperties=font_bold.prop, transform=fig.transFigure)
    else:
        # All other positions: 4 groups of 3 metrics each
        if position == 'FB':
            categories = ["PASSING", "CARRYING", "DEFENDING", "CREATIVITY"]
        elif position == '#6':
            categories = ["SECURITY", "PROGRESSION", "DEFENDING", "DUELLING"]
        elif position == '#8':
            categories = ["SECURITY", "PROGRESSION", "DEFENDING", "CREATIVITY"]
        elif position == 'WF/AM':
            categories = ["GOALSCORING", "CREATIVITY", "PENETRATION", "DRIBBLING"]
        elif position == 'CF':
            categories = ["GOALS", "CREATIVITY", "OUTLET", "PRESSING"]
        else:
            categories = [f"POSITION: {position}", "PERCENTILES", "", ""]
        
        colors = ["#5D688A", "#F7A5A5", "#FFDBB6", "#6B2C91"]
        
        # Calculate evenly spaced positions for 4 categories
        total_width = 0.5  # Reduced width for tighter spacing
        start_x = 0.5 - (total_width / 2)  # Start position (centered)
        spacing = total_width / (len(categories) - 1) if len(categories) > 1 else 0
        
        for i, (category, color) in enumerate(zip(categories, colors)):
            if category:  # Only add non-empty categories
                x_pos = start_x + (i * spacing)
                fig.text(x_pos, categories_y, category, size=14, color=color, 
                        ha="center", va="center", fontproperties=font_bold.prop, transform=fig.transFigure)
    return fig


def display_radar_in_streamlit(radar_data):
    """
    Display the radar chart in Streamlit with download option
    
    Args:
        radar_data (dict): Dictionary containing player data from session state
    """
    import io
    
    try:
        # Generate the radar
        fig = generate_radar(radar_data)
        
        # Display in Streamlit
        st.pyplot(fig)
        
        # Save to buffer for download
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        
        # Download button
        st.download_button(
            label="📥 Download Radar Chart",
            data=img_buffer,
            file_name=f"{radar_data['player_name']}_{radar_data['position']}_radar.png",
            mime="image/png"
        )
        
        # Close the figure to free memory
        plt.close(fig)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error generating radar: {str(e)}")
        return False