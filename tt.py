import streamlit as st
import os
import subprocess
import time
import signal
import pandas as pd
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import schedule

# Function to validate check-in and check-out dates
def validate_dates(checkin_date_str, checkout_date_str):
    today = datetime.today().date()
    checkin_date = datetime.strptime(checkin_date_str, '%Y-%m-%d').date()
    checkout_date = datetime.strptime(checkout_date_str, '%Y-%m-%d').date()

    if checkin_date <= today:
        raise ValueError("Check-in date must be greater than today's date.")
    if checkout_date <= checkin_date:
        raise ValueError("Check-out date must be greater than check-in date.")

# Function to fetch hotels using Playwright
def fetch_hotels(city, checkin_date, checkout_date):
    city = city.capitalize()
    page_url = f'https://www.booking.com/searchresults.en-us.html?checkin={checkin_date}&checkout={checkout_date}&selected_currency=PKR&ss={city}&ssne={city}&ssne_untouched={city}&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(page_url, timeout=60000)
        time.sleep(10)
        hotels_list = []

        while True:
            print(f'Processing page with {len(hotels_list)} entries.')

            try:
                hotels = page.locator('div[data-testid="property-card"]').all()
                print(f'There are {len(hotels)} hotels on this page.')

                for hotel in hotels:
                    hotel_dict = {}
                    try:
                        hotel_dict['hotel'] = hotel.locator('div[data-testid="title"]').inner_text() if hotel.locator('div[data-testid="title"]').count() > 0 else 'N/A'
                        hotel_dict['price'] = hotel.locator('span[data-testid="price-and-discounted-price"]').inner_text() if hotel.locator('span[data-testid="price-and-discounted-price"]').count() > 0 else 'N/A'
                        hotel_dict['score'] = hotel.locator('div[data-testid="review-score"] > div:first-of-type').inner_text() if hotel.locator('div[data-testid="review-score"] > div:first-of-type').count() > 0 else 'N/A'
                        hotel_dict['avg review'] = hotel.locator('div[data-testid="review-score"] > div:nth-of-type(2) > div:first-of-type').inner_text() if hotel.locator('div[data-testid="review-score"] > div:nth-of-type(2) > div:first-of-type').count() > 0 else 'N/A'
                        hotel_dict['reviews count'] = hotel.locator('div[data-testid="review-score"] > div:nth-of-type(2) > div:nth-of-type(2)').inner_text().split()[0] if hotel.locator('div[data-testid="review-score"] > div:nth-of-type(2) > div:nth-of-type(2)').count() > 0 else 'N/A'
                        hotel_dict['distance'] = hotel.locator('span[data-testid="distance"]').inner_text() if hotel.locator('span[data-testid="distance"]').count() > 0 else 'N/A'
                        hotel_dict['address'] = hotel.locator('span[data-testid="address"]').inner_text() if hotel.locator('span[data-testid="address"]').count() > 0 else 'N/A'
                        hotel_dict['description'] = hotel.locator('div[class*="c777ccb0a3"]').inner_text() if hotel.locator('div[class*="c777ccb0a3"]').count() > 0 else 'N/A'
                        hotel_dict['Availability'] = hotel.locator('div[class*="c6f064a3e8"]').inner_text() if hotel.locator('div[class*="c6f064a3e8"]').count() > 0 else 'N/A'

                    except Exception as e:
                        print(f"An error occurred while processing a hotel: {e}")
                        hotel_dict['hotel'] = 'Error'
                        hotel_dict['price'] = 'Error'
                        hotel_dict['score'] = 'Error'
                        hotel_dict['avg review'] = 'Error'
                        hotel_dict['reviews count'] = 'Error'
                        hotel_dict['distance'] = 'Error'
                        hotel_dict['address'] = 'Error'
                        hotel_dict['description'] = 'Error'
                        hotel_dict['Availability'] = 'Error'

                    hotels_list.append(hotel_dict)

            except Exception as e:
                print(f"An error occurred while processing hotels: {e}")
                break

            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(10)
                new_hotels = page.locator('div[data-testid="property-card"]').all()
                if len(new_hotels) <= len(hotels_list):
                    print("No new hotels loaded. Ending scrape.")
                    break
            except Exception as e:
                print(f"An error occurred while scrolling or loading more hotels: {e}")
                break

        df = pd.DataFrame(hotels_list)
        output_dir = os.path.join('excel_file_of_city', city)
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f'{city}-hotels_list.xlsx')
        df.to_excel(file_path, index=False)
        browser.close()

# Function to run the scheduled job
def scheduled_job():
    # Read city and time from text files
    with open('city.txt', 'r') as city_file:
        cities = [line.strip() for line in city_file.readlines()]
        print(cities)

    with open('time.txt', 'r') as time_file:
        t = time_file.read().strip()
        print(t)

    today = datetime.today().date()
    checkin_date = today + timedelta(days=1)
    checkout_date = today + timedelta(days=2)

    checkin_date_str = checkin_date.strftime('%Y-%m-%d')
    checkout_date_str = checkout_date.strftime('%Y-%m-%d')

    try:
        validate_dates(checkin_date_str, checkout_date_str)
    except ValueError as e:
        print(f"Date validation error: {e}")
        return

    for city in cities:
        print(f"Fetching hotels for {city}...")
        fetch_hotels(city, checkin_date_str, checkout_date_str)
    print("\n\t\t ******** Task Assigned done for today ********* \n")

# Streamlit UI
st.title('Hotel Scraper Scheduler')

# Input fields for cities
st.subheader('Add Cities:')
cities_input = st.text_area('Enter cities (one per line):', height=150)
cities = [city.strip() for city in cities_input.splitlines() if city.strip()]

# Input field for time
time_input = st.text_input('Enter Time (HH:MM):', '')

if st.button('Save and Start Scraping'):
    if cities and time_input:
        with open('city.txt', 'w') as city_file:
            city_file.write('\n'.join(cities))
        with open('time.txt', 'w') as time_file:
            time_file.write(time_input)
        
        st.write('Cities and Time saved. Starting scraping...')

        # Schedule and run the job
        try:
            schedule.every().day.at(time_input).do(scheduled_job)
            while True:
                schedule.run_pending()
                time.sleep(60)  # Wait a minute
        except Exception as e:
            st.error(f'An error occurred: {e}')
    else:
        st.error('Please enter both cities and time.')
