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
    
    # Extract data from the radar_data dictionary
    player_name = radar_data['player_name']
    position = radar_data['position']
    params = radar_data['params']
    percentiles = radar_data['percentiles']
    
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
            ["#000000"] * 12   # Black text on green
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
            ["#FFF2EF"] * 3    # Blue for defensive
        )
        text_colors = (
            ["#000000"] * 12
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
        inner_circle_size=10,
    )
    
    # Generate the pizza plot
    fig, ax = baker.make_pizza(
        percentiles,  # Use percentiles for radar visualization
        figsize=(8, 8),  # Adjusted for better Streamlit display
        slice_colors=slice_colors,
        value_colors=text_colors,
        value_bck_colors=slice_colors,
        blank_alpha=0.4,
        kwargs_slices=dict(
            edgecolor="#000000", zorder=2, linewidth= 2
        ),
        kwargs_params=dict(
            color="#000000", fontsize=9,
            va="center", fontweight="bold"
        ),
        kwargs_values=dict(
            color="#000000", fontsize=8,
            zorder=3, fontweight="bold",
            bbox=dict(
                edgecolor="#000000", facecolor="cornflowerblue",
                boxstyle="round,pad=0.2", lw=1
            )
        )
    )
    
    # Add the AU logo to the center of the radar
    try:
        logo_path = Path(__file__).parent / "AULogo.png"
        
        if logo_path.exists():
            # Load the logo as PIL Image
            logo_image = Image.open(logo_path)
            
            # Add the logo to the center of the radar
            add_image(
                logo_image, fig, left=0.4775, bottom=0.46, width=0.07, height=0.07,
                alpha=1
            )
            
    except Exception as e:
        # Show error for debugging
        try:
            import streamlit as st
            st.error(f"Logo loading error: {e}")
        except:
            print(f"Error loading logo: {e}")
    
    # Add title and subtitle with position-specific context
    fig.text(
        0.5, 0.985, f"{player_name.upper()} | {position} TEMPLATE", size=15,
        color="#000000", ha="center", va="center", fontweight="bold"
    )

    # Position-specific subtitle with color-coded categories
    if position == 'CB':
        # CB has 3 groups of 4 metrics each with different colors
        fig.text(0.5, 0.95, "DEFENDING", size=10, color="#5D688A", ha="center", va="center", fontweight="bold", transform=fig.transFigure)
        fig.text(0.5, 0.935, "•", size=10, color="#000000", ha="center", va="center", fontweight="bold", transform=fig.transFigure)
        fig.text(0.5, 0.92, "DUELLING", size=10, color="#F7A5A5", ha="center", va="center", fontweight="bold", transform=fig.transFigure)
        fig.text(0.5, 0.905, "•", size=10, color="#000000", ha="center", va="center", fontweight="bold", transform=fig.transFigure)
        fig.text(0.5, 0.89, "BALL PLAYING", size=10, color="#FFDBB6", ha="center", va="center", fontweight="bold", transform=fig.transFigure)
    else:
        # All other positions: 4 groups of 3 metrics each
        if position == 'FB':
            categories = ["PASSING", "CARRYING", "DEFENDING", "CREATIVITY"]
        elif position == '#6':
            categories = ["BALL SECURITY", "PROGRESSION", "DEF. ACTIVITY", "DUEL SUCCESS"]
        elif position == '#8':
            categories = ["BALL SECURITY", "PROGRESSION", "DEFENSIVE", "CREATIVITY"]
        elif position == 'WF/AM':
            categories = ["GOALSCORING", "CREATIVITY", "PENETRATION", "DRIBBLING"]
        elif position == 'CF':
            categories = ["GOALSCORING", "CREATIVITY", "OUTLET", "PRESSING"]
        else:
            categories = [f"POSITION: {position}", "PERCENTILES", "", ""]
        
        colors = ["#5D688A", "#F7A5A5", "#FFDBB6", "#FFF2EF"]
        
        # Create colored text for each category
        y_positions = [0.95, 0.935, 0.92, 0.905]
        for i, (category, color) in enumerate(zip(categories, colors)):
            if category:  # Only add non-empty categories
                fig.text(0.5, y_positions[i], category, size=10, color=color, 
                        ha="center", va="center", fontweight="bold", transform=fig.transFigure)
                if i < len(categories) - 1 and categories[i+1]:  # Add separator if not last
                    fig.text(0.5, y_positions[i] - 0.007, "•", size=10, color="#000000", 
                            ha="center", va="center", fontweight="bold", transform=fig.transFigure)
    

    
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