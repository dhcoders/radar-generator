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
from src.wyscout_remapping import wyscout_column_mapping


#HANDLING IMPORTING WYSCOUT DATA

st.header("📁 WSL2 WYSCOUT RADAR GENERATOR")
st.markdown(f"Upload your Wyscout export (Excel or CSV format) and select a position, then player, to generate a radar chart.")
st.markdown(f"There are no sample tweaking features, so make sure you get your sample right BEFORE importing data & using this tool.")
uploaded_file = st.file_uploader(
    "Choose a file",
    type=['xlsx', 'xls', 'csv'],
    help="Upload a Wyscout export containing player data. Please output ALL AVAILABLE METRICS IF POSSIBLE"
)

#Turn the uploaded file into a dataframe so we can use it
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success("File uploaded successfully!")
        
        # Apply column remapping to make radar labels more readable
        df = df.rename(columns=wyscout_column_mapping)
        st.info(f"✅ Column names remapped for better readability")

        #Transforming the dataframe to input new metrics into the df for the radars - BEFORE WE DO THE PERCENITLES

        # EFx Aerial Duels
        df['Aerial Duels Won'] = (df['Aerial Duels'] * df['Aerial Duels Won %']) / 100
        # EFx Ground Duels
        df['Ground Duels Won'] = (df['Ground Duels'] * df['Ground Duels Won %']) / 100
        # EFx Duels - Essentially total duels won.
        df['Total Duels Won'] = (df['Ground Duels Won'] + df['Aerial Duels Won'])
        # Total Duel %
        df['Total Duel %'] = (df['Aerial Duels Won %'] + df['Ground Duels Won %']) / 2
        #Total Duels per 90
        df['Duels Contested'] = df['Aerial Duels'] + df['Ground Duels']
        # EFx Prog. Pass
        df['EFx Prog. Pass'] = (df['Prog. Passes'] * df['Prog. Pass Acc. %']) / 100
        #xG per Shot
        df['xG per Shot'] = df['xG'] / df['Shots']
        #Finishing 
        df['NPG-xG'] = df['Total Non-Pen. Goals'] - df['Total xG']

    


        # Calculate percentiles for ALL numeric columns NOW, then we can grab them for the radar later
        lower_is_better = ['Dispossessed', 'Yellow cards', 'Red cards', 'Fouls']  # If having a metric lower is preferable, this list signals that so later code can invert the percentile
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        #Code for calculating percentile ranks across the data.
        for col in numeric_columns:
            percentiles = []
            #This section handles any null values - converting them to 0s
            for value in df[col]:
                if pd.isna(value):  # Check if value is NaN
                    percentiles.append(0)  # makes the NaN values 0 - we can adjust this if need be.
                else:
                    percentile = stats.percentileofscore(df[col].dropna(), value)  # Use dropna() for clean calculation
                    if col in lower_is_better:
                        percentile = 100 - percentile
                    percentiles.append(math.floor(percentile))
            df[f'{col}_percentile'] = percentiles


        # Player selection with search/type features - USE THIS TO SELECT THE PLAYER YOU WANT TO GENERATE A RADAR FOR
        if 'Player' in df.columns:
            players = sorted(df['Player'].unique())
            
            selected_player = st.selectbox(
                "🔍 Search and select a player:",
                options=players,
                help="Type to search for a player name"
            )
            
            if selected_player:
                st.write(f"Selected: **{selected_player}**")
                # You'll use this selected_player variable for radar generation later
                
        else:
            st.error("❌ No 'Player' column found. Make sure this is a Wyscout player export.")
            
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")


#This is the list of metrics that will be used to generate the radar.
POSITION_TEMPLATES = {
    'CB': ['Succ. Def. Actions', 'Shot Blocked', 'Interceptions','Fouls', 'Ground Duels Won %', 'Aerial Duels Won %', 'Ground Duels', 'Aerial Duels', 
           'Prog. Passes', 'Prog. Pass Acc. %', 'Prog. Carries', 'Dribble Succ. %'],
    
    'FB': ['Shorter Pass Acc. %', 'Prog. Passes', 'Prog. Pass Acc. %', 'Prog. Carries', 'Dribble', 'Dribble Succ. %',
           'Succ. Def. Actions', 'Ground Duels Won %', 'Aerial Duels Won %', 'Assists', 'xA', 'Shots Created'],
    
    '#6': ['Passes', 'Pass Acc. %', 'Dribble Succ. %', 'Prog. Passes', 'Prog. Pass Acc. %',
           'Prog. Carries', 'Ground Duels', 'Interceptions', 'Succ. Def. Actions', 'Ground Duels Won %', 'Aerial Duels Won %', 'Fouls'],
    
    '#8': ['Passes', 'Pass Acc. %', 'Dribble Succ. %', 'Prog. Passes', 'Prog. Pass Acc. %',
           'Prog. Carries', 'Ground Duels', 'Interceptions', 'Succ. Def. Actions', 'xG', 'xA', 'Shots Created'],
    
    'WF/AM': ['Goals', 'xG', 'Shots', 'Assists', 'xA', 'Shots Created', 
              'Prog. Passes', 'Prog. Carries', 'Passes to PA',
              'Dribble', 'Dribble Succ. %', 'Fouls Drawn'],
    
    'CF': ['Goals', 'xG', 'NPG-xG', 'Assists', 'xA', 'Passes to PA',
           'Long Passes Received', 'Aerial Duels Won', 'Dribble Succ. %', 'Ground Duels', 'Interceptions', 'Succ. Def. Actions'],
}

selected_template = st.selectbox("Choose radar type:", POSITION_TEMPLATES.keys())
params = POSITION_TEMPLATES[selected_template]

# Combined Step 4 & 5: Extract data AND generate radar in one click
if uploaded_file is not None and 'selected_player' in locals():
    if st.button("🚀 Generate Radar Chart", type="primary"):
        with st.spinner("Extracting data and generating radar..."):
            # Get the selected player's data
            player_data = df[df['Player'] == selected_player].iloc[0]
            
            # Extract values and percentiles for the selected template
            values = []
            percentiles = []
            param_names = []
            
            for param in params:
                if param in df.columns:
                    # Get the actual value
                    actual_value = player_data[param]
                    values.append(actual_value)
                    
                    # Get percentile if it exists
                    percentile_col = f'{param}_percentile'
                    if percentile_col in df.columns:
                        percentile_value = player_data[percentile_col]
                        percentiles.append(percentile_value)
                    else:
                        percentiles.append(50)  # Default to 50th percentile if not found
                    
                    param_names.append(param)
                else:
                    st.warning(f"⚠️ Parameter '{param}' not found in data")
            
            # If we have valid data, generate the radar immediately
            if values:
                # Prepare radar data
                radar_data = {
                    'player_name': selected_player,
                    'position': selected_template,
                    'params': param_names,
                    'values': values,
                    'percentiles': percentiles,
                    'player_data': player_data
                }
                
                # Import and generate radar
                # Generate radar directly instead of importing
                try:
                    import io
                    from src.radar_maker import generate_radar
                    
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
                    
                    success = True
                    
                except Exception as e:
                    st.error(f"❌ Error generating radar: {str(e)}")
                    success = False

                    st.markdown("Metric categories (under player name on radar) are from 12 o'clock and run clockwise.")

# Optional: Reset button
st.markdown("---")
if st.button("🔄 Start Over", type="secondary"):
    st.experimental_rerun()
