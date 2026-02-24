#!/usr/bin/env powershell

Write-Host "Setting up offline matplotlib environment..." -ForegroundColor Green
$env:MPLCONFIGDIR = "$env:TEMP\mpl-offline"
$env:FONTCONFIG_PATH = "fonts"

Write-Host "Launching Streamlit app..." -ForegroundColor Green
streamlit run enhanced_app.py