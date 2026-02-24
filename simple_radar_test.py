#!/usr/bin/env python3
"""
Simple radar chart test using only matplotlib (no mplsoccer)
"""

import matplotlib.pyplot as plt
import numpy as np
from math import pi

def create_simple_radar(values, labels, player_name="Test Player"):
    """Create a simple radar chart using matplotlib only"""
    
    # Number of variables
    N = len(labels)
    
    # Compute angle for each axis
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # Complete the circle
    
    # Add values for completion
    values += values[:1]
    
    # Initialize the plot
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # Draw the plot
    ax.plot(angles, values, 'o-', linewidth=2, label=player_name)
    ax.fill(angles, values, alpha=0.25)
    
    # Add labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    
    # Set y-axis limits
    ax.set_ylim(0, 100)
    
    # Add title
    plt.title(f"{player_name} - Performance Radar", size=16, y=1.1)
    
    return fig

if __name__ == "__main__":
    # Test data
    test_labels = ['Speed', 'Shooting', 'Passing', 'Defending', 'Dribbling', 'Crossing']
    test_values = [85, 70, 90, 60, 88, 75]
    
    print("Creating simple radar...")
    fig = create_simple_radar(test_values, test_labels, "Test Player")
    
    print("Saving radar...")
    fig.savefig("test_radar.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    print("Simple radar created successfully!")