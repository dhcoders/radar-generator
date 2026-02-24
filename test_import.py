#!/usr/bin/env python3

print("Starting imports...")

try:
    import pandas as pd
    print("OK pandas imported")
except Exception as e:
    print(f"FAIL pandas failed: {e}")

try:
    import numpy as np
    print("OK numpy imported")
except Exception as e:
    print(f"FAIL numpy failed: {e}")

try:
    import matplotlib.pyplot as plt
    print("OK matplotlib imported")
except Exception as e:
    print(f"FAIL matplotlib failed: {e}")

try:
    print("Importing mplsoccer...")
    from mplsoccer import PyPizza
    print("OK mplsoccer imported")
except Exception as e:
    print(f"FAIL mplsoccer failed: {e}")

print("All imports completed")