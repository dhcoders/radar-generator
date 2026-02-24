#!/usr/bin/env python3
"""
Launch script for the radar app that sets up the offline matplotlib environment
"""

import os
import sys
import tempfile
import subprocess

def main():
    print("Setting up offline matplotlib environment...")
    
    # Set environment variables to prevent font downloads
    os.environ['MPLCONFIGDIR'] = os.path.join(tempfile.gettempdir(), 'mpl-offline')
    os.environ['FONTCONFIG_PATH'] = 'fonts'
    
    print("Launching Streamlit app...")
    
    # Launch streamlit with the current environment
    try:
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'enhanced_app.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error launching app: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nApp stopped by user")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())