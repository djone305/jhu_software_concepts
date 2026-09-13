'''
Donnell Jones
EN.605.256.83.FA26
Section 83
Module 2 - Assignment: Web Scraping - Part 1 (Scrape Data)
Revision: New
Date: 09/13/2026
'''

# Import libraries
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import json

if __name__ == "__main__":
   
    # Open the browser
    driver = uc.Chrome()

    # Load the page and wait for the JavaScript to populate the data
    try:
        # Navigate to website
        print("Loading page...")
        driver.get("https://www.thegradcafe.com/survey")

        # Wait for survey results
        time.sleep(10)

        # Grab dynamic HTML directly from Selenium 
        html_content = driver.page_source

    finally:
        # Close the browser session
        #driver.quit()
        pass

    # Parse the HTML with BeautifulSoup
    survey_html = BeautifulSoup(html_content, "html.parser")

    page_text = survey_html.get_text()

    print(page_text)

# Create list of parameters to search website with using mechanical soup
# Create for loop to query webiste
# Parse data using BeautifulSoup
# Save parsed data as JSON file

# Function for scraping website
def scrape():
    pass

# Function to save scraped data
def save_data():
    pass

################################################################################
def main():
   pass

if __name__ == "__main__":
  main()