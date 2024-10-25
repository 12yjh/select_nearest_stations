
# -*- coding: utf-8 -*-
"""
Created on Mon May 27 13:40:09 2024

@author: yjh12

Process the grid table and subway station table, assign them numbers, and find the nearest subway station for each grid.
Note: Manual sampling verification has been performed.
"""
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import electrocardiogram
from scipy.signal import find_peaks
import os
import datetime
import requests
import sys
# Import tushare

import json
import numpy as np

df_grid = pd.read_csv('res_select_nearest_stations/※Walking to Subway Station within 30 Minutes_ Urban Area 0816.csv')
subway_read = pd.read_csv('res_select_nearest_stations/Subway_stations202107.csv')  # encoding='gbk'
#%%
# Test whether the distance between two coordinates is 1000 meters
from geopy.distance import geodesic

def cor_distance(coord1, coord2):
    """
    Calculate the distance between two coordinates.

    Parameters:
    coord1: Tuple representing the first coordinate in the format (latitude, longitude)
    coord2: Tuple representing the second coordinate in the format (latitude, longitude)

    Returns:
    Distance in kilometers.
    """
    return geodesic(coord1, coord2).kilometers
 

#%% 1. Generate Grid Latitude and Longitude Table%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Add a column `grid_no` in `df_grid` to store the sequence number of each grid.
df_grid['grid_no'] = df_grid.index + 1  

# #%% 2. Process Subway Station Data%%%%%%%%%%%%%%%%%%%%%%%

subway = subway_read.copy()

# Add a column `subway_no` in `subway` to store the sequence number of each subway station.
subway['subway_no'] = subway.index + 1  

# Convert the data type of the `subway_no` column to string.
subway['subway_no'] = subway['subway_no'].astype(str)

#%% 3. Calculate the Impact of Subway Stations on Grids%%%%%%%%%%%%%%%%%%%%%%%%
# There are three loops: 1). Iterate through all 1000x1000 grids. 2). Generate 100 points for all grids. 3). Iterate through all subway stations

# 1). Loop through grids：Iterate through all 1000x1000 grids.
subway_impact = 800  # Set the impact distance of subway stations to 800 meters
big_range = 0.025  # For coarse screening, set the latitude and longitude range that subway stations can influence to 0.025, because at 0.02, there are still areas within a 30-minute walk from subway stations that are not within the influence range of any subway station

coord1 = (30,120) # Coordinate point 1 used for distance measurement. 
coord2 = (30,120+big_range )  # Coordinate point 2 used for distance measurement.
distance = cor_distance(coord1, coord2)
print("Distance:", distance, "kilometers")

  # Loop through each row of the `df_grid` table.
  # Coarse screen the main subway stations to improve runtime speed.
  # Here, conditional filtering is used to select subway stations within a certain range of the current grid.
 
# Start a loop to iterate through each row of the `df_grid` DataFrame
for grid_no in range( len(df_grid)):

# Filter out subway stations within a certain range of the current grid and store them in `subway_hold`.
    subway_hold = subway[(subway['X']<df_grid.loc[grid_no,'right_lon']+big_range) \
                          &(subway['X']>df_grid.loc[grid_no,'left_lon']-big_range)\
                          &(subway['Y']<df_grid.loc[grid_no,'up_la']+big_range)\
                          &(subway['Y']>df_grid.loc[grid_no,'down_la']-big_range)] #  X 119 Y 30

# Concatenate the names and sequence numbers of the filtered subway stations into strings.
    name_string = ', '.join(subway_hold['name'])
    no_string = ', '.join(subway_hold['subway_no'])

# Check if `subway_hold` is not empty, and if not, process the subway influence area.
    if not subway_hold.empty:

# Add the concatenated subway station names, count, and sequence numbers to the corresponding row in the `df_grid` DataFrame.
        df_grid.loc[grid_no,'good_subway'] = name_string  # Concatenated subway station names
        df_grid.loc[grid_no,'good_subway_count'] = len(subway_hold['name'])  # Number of subway stations
        df_grid.loc[grid_no,'good_subway_no'] = no_string  # Concatenated subway station sequence numbers
    pass

# Export the `df_grid` and `subway` DataFrames to CSV files.
# df_grid.to_csv('8.9.1v2 Temporary_Nearby Subway Stations 0828.csv', index=False, encoding='utf-8-sig')
# subway.to_csv('8.9.2v2 df_subway.csv')
# **********************************************************************************
#%% Copy `df_grid` and filter out rows where `good_subway_count` is not null, then reset the index. This is to check if the coarse screening range for `df_grid` is appropriate.
df_grid2 = df_grid.copy()
df_grid2 = df_grid2[df_grid2['good_subway_count'].notnull()]
df_grid2 = df_grid2.reset_index(drop=True)
#%%
# Try running a part of the code
# df_grid2 = df_grid2.iloc[:,:]  #[:,:], here no column indices are specified, meaning all columns are selected.

#%%
for i in df_grid2.index: # Iterate through all indexes (i.e., all rows) in the table

    lon = df_grid2.loc[i,'lon']  # Locate the `lon` value of row `i`
    la = df_grid2.loc[i,'la'] 
    
    list_sub = df_grid2.loc[i,'good_subway_no']
    # Split the string `list_sub` by commas into multiple substrings and store them in a list
    sub_list = list_sub.split(',') 
    # List comprehension to strip leading and trailing whitespace (including spaces, tabs, etc.) from each element in `sub_list`.
    sub_list = [item.strip() for item in sub_list]
    # `isin(sub_list)` is a function call that checks if each value in the `subway_no` column exists in the `sub_list`. If it does, the corresponding row is selected.
    sub = subway[subway['subway_no'].isin(sub_list)]
    # sub = subway[subway['subway_no'] == list_sub]  
    # sub = subway[subway['subway_no'] == [22,]]  
    
    
    # Calculate distances and add them to the DataFrame
    sub['distance'] = sub.apply\
        (lambda row: cor_distance((row['Y'], row['X']), (la, lon)), axis=1)
    # The `row` parameter in the lambda function represents the current row in the DataFrame, and you can access its column values, such as `row['Y']` and `row['X']`.
    # Print results for checking
    # print(sub)
    
    # Find the index of the minimum value in the 'distance' column
    min_distance_index = sub['distance'].idxmin()
    
    # Get the row with the minimum distance using the index
    min_distance_row = sub.loc[min_distance_index]
    
    # Extract the value of the `subway_no` column
    min_subway_no = min_distance_row['subway_no']
    df_grid2.loc[i,'nearest_sub'] = min_subway_no

# Merge based on the `nearest_sub` column and the `subway_name` column in the `subway` table
df_merged = pd.merge(df_grid2, subway, left_on='nearest_sub', right_on='subway_no', how='left')

# Select the required columns, including all columns from `df_grid2` and the `subway_no`, `X`, `Y` columns from the `subway` table
df_final = df_merged[
    df_grid2.columns.tolist() + ['subway_no', 'X', 'Y']
]

# df_final.to_csv('8.9.3v2 Nearest Subway Station 0828.csv', index=False, encoding='utf-8-sig')