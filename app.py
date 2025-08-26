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


#HANDLING IMPORTING WYSCOUT DATA

st.header("📁 WSL2 WYSCOUT RADAR GENERATOR")
st.markdown(f"Upload your Wyscout export (Excel or CSV format) and select a position, then player, to generate a radar chart.")
st.markdown(f"There are no sample tweaking features, so make sure you get your sample right BEFORE importing data & using this tool!")
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

        #Transforming the dataframe to input new metrics into the df for the radars - BEFORE WE DO THE PERCENITLES

            # EFx Aerial Duels
        df['Aerial Duels Won'] = (df['Aerial duels per 90'] * df['Aerial duels won, %']) / 100
        # EFx Ground Duels
        df['Ground Duels Won'] = (df['Defensive duels per 90'] * df['Defensive duels won, %']) / 100
        # EFx Duels - Essentially total duels won.
        df['Total Duels Won'] = (df['Ground Duels Won'] + df['Aerial Duels Won'])
        # Total Duel %
        df['Total Duel %'] = (df['Aerial duels won, %'] + df['Defensive duels won, %']) / 2
        #Total Duels per 90
        df['Duels Contested'] = df['Aerial duels per 90'] + df['Defensive duels per 90']
        # EFx Prog. Pass
        df['EFx Prog. Pass'] = (df['Progressive passes per 90'] * df['Accurate progressive passes, %']) / 100
        #xG per Shot
        df['xG per Shot'] = df['xG per 90'] / df['Shots per 90']
        #Finishing 
        df['NPG-xG'] = df['Non-penalty goals'] - df['xG']

        # Calculate percentiles for ALL numeric columns NOW, then we can grab them for the radar later
        lower_is_better = ['Dispossessed', 'Yellow cards', 'Red cards']  # If having a metric lower is preferable, this list signals that so later code can invert the percentile
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
    'CB': ['Successful defensive actions per 90', 'Shots blocked per 90', 'Interceptions per 90','Fouls per 90', 'Defensive duels won, %', 'Aerial duels won, %', 'Defensive duels per 90', 'Aerial duels per 90', 
           'Progressive passes per 90', 'Accurate progressive passes, %', 'Progressive runs per 90', 'Successful dribbles, %'],
    
    'FB': ['Accurate short / medium passes, %', 'Progressive passes per 90', 'Accurate progressive passes, %', 'Progressive runs per 90', 'Dribbles per 90', 'Successful dribbles, %',
           'Successful defensive actions per 90', 'Defensive duels won, %', 'Aerial duels won, %', 'Assists', 'xA per 90', 'Key passes per 90'],
    
    '#6': ['Passes per 90', 'Accurate passes, %', 'Successful dribbles, %', 'Progressive passes per 90', 'Accurate progressive passes, %',
           'Progressive runs per 90', 'Defensive duels per 90', 'Interceptions per 90', 'Successful defensive actions per 90', 'Defensive duels won, %', 'Aerial duels won, %', 'Fouls per 90'],
    
    '#8': ['Passes per 90', 'Accurate passes, %', 'Successful dribbles, %', 'Progressive passes per 90', 'Accurate progressive passes, %',
           'Progressive runs per 90', 'Defensive duels per 90', 'Interceptions per 90', 'Successful defensive actions per 90', 'xG per 90', 'xA per 90', 'Key passes per 90'],
    
    'WF/AM': ['Goals', 'xG per 90', 'Shots per 90', 'Assists', 'xA per 90', 'Key passes per 90', 
              'Progressive passes per 90', 'Progressive runs per 90', 'Passes to penalty area per 90'
              'Dribbles per 90', 'Successful dribbles, %', 'Fouls suffered per 90'],
    
    'CF': ['Goals', 'xG per 90', 'NPG-xG', 'Assists', 'xA per 90', 'Passes to penalty area per 90',
           'Received long passes per 90', 'Aerial Duels Won', 'Successful dribbles, %', 'Defensive duels per 90', 'Interceptions per 90', 'Successful defensive actions per 90'],
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
