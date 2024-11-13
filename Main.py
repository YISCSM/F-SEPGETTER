import pandas as pd
import requests
from datetime import datetime
import time
import os
import streamlit as st

# Function to retrieve the table from the webpage
def get_table(date):
    # Extract details from date to generate link
    day = date.day
    month = date.month
    year = date.year
    
    # Build URL
    url = f'https://www.federalreserve.gov/monetarypolicy/fomcprojtabl{year}{month:02d}{day:02d}.htm'
    
    # Set headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.69 Safari/537.36'
    }
    
    # Make the request with headers
    response = requests.get(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Read HTML table from the response content
        df_list = pd.read_html(response.content)
        df = df_list[0]  # Assume the first table is the desired one
        # Combine the two levels with an underscore, for example
        df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns.values]
        return df
    else:
        return None  # Return None if the table could not be retrieved

# Function to apply conditions to change values
def assign_direction(change_value):
    if pd.isna(change_value):  # Handle NaN values
        return None
    elif change_value < -0.5:
        return 'Big Dove'
    elif change_value < -0.25:
        return 'Dove'
    elif change_value > 0.5:
        return 'Big Hawk'
    elif change_value > 0.25:
        return 'Hawk'
    else:
        return None

# Function to calculate the rate changes and assign directions
def get_rate(df):
    # Filter rows from 9 to 11
    df_filtered = df[9:11]
    
    # Select the first five columns
    df_filtered = df_filtered.iloc[:, :5]
    
    # Convert columns 1 to 4 to integer type
    df_filtered.iloc[:, 1:5] = df_filtered.iloc[:, 1:5].astype(float)
    df_filtered = df_filtered.set_index(df.columns[0])
    
    df_filtered.loc['Change'] = df_filtered.iloc[0] - df_filtered.iloc[1]
    
    # Apply the function to the 'Change' row and create a new row 'Direction'
    df_filtered.loc['Direction'] = df_filtered.loc['Change'].apply(assign_direction)

    return df_filtered

# Function to log the time of retrieval
def log_time(time_str):
    log_folder = 'logs'
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)  # Create logs folder if it doesn't exist
    
    log_file = os.path.join(log_folder, 'retrieval_log.txt')
    
    with open(log_file, 'a') as file:
        file.write(f"Data retrieved at: {time_str}\n")

# Function to check for data and return the DataFrame
def check_for_data(date):
    # Retrieve the table
    df = get_table(date)
    
    if df is not None:
        rate = get_rate(df)
        return rate
    else:
        return None  # If no data is found, return None

# Streamlit app layout
st.title("FOMC SEP Data Checker")

# Date input for the user to select the SEP date
date_input = st.date_input("Enter the date of the SEP you want")
date = datetime.strptime(str(date_input), "%Y-%m-%d")

# Display the selected date
st.write(f"You selected: {date.strftime('%B %d, %Y')}")

# Button to fetch data
if st.button("Fetch Data"):
    # Retrieve the data based on the selected date
    df = check_for_data(date)
    
    if df is not None:
        # Show the retrieved data
        # Format the DataFrame for display
        formatted_df = df.copy()
        
        # Format the 'Change' row values to 2 decimal places
        formatted_df.loc['Change'] = formatted_df.loc['Change'].apply(lambda x: f"{x:.2f}")

        st.write(formatted_df)
        
        # Log the retrieval time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_time(current_time)
        st.write(f"Data retrieved at: {current_time}")
    else:
        st.error("Data could not be retrieved. Please check the date or try again later.")
