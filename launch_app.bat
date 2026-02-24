@echo off
echo Setting up offline matplotlib environment...
set MPLCONFIGDIR=%TEMP%\mpl-offline
set FONTCONFIG_PATH=fonts

echo Launching Streamlit app...
streamlit run enhanced_app.py

pause