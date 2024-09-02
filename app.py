import streamlit as st
import os
import subprocess
import time
import signal

def save_inputs(cities, time):
    with open('city.txt', 'w') as city_file:
        city_file.write('\n'.join(cities))
    with open('time.txt', 'w') as time_file:
        time_file.write(time)

def run_scraping_script():
    # Ensure that 'main.py' is the name of your scraping script
    subprocess.run(['python', 'main.py'], check=True)

st.title('Hotel Scraper Scheduler')

# Input fields for cities
st.subheader('Add Cities:')
cities = st.text_area('Enter cities (one per line):', height=150).splitlines()

# Input field for time
time = st.text_input('Enter Time (HH:MM):', '')

if st.button('Save and Exit'):
    if cities and time:
        save_inputs(cities, time)
        st.write('Cities and Time saved. Closing application...')
        run_scraping_script()
        # Close Streamlit
        st.stop()  # This will stop the Streamlit app
        
        # Run the scraping script
        
        
    else:
        st.error('Please enter both cities and time.')
