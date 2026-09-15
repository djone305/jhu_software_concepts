'''
Donnell Jones
EN.605.256.83.FA26
Section 83
Module 2 - Assignment: Web Scraping - Part 1 (Scrape Data)
Revision: New
Date: 09/13/2026
'''

# Import libraries
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

if __name__ == "__main__":
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking")

    
    # Open the browser
    driver = uc.Chrome(options=options)

    try:
        # Load the page and wait for the JavaScript to populate the data

        # Navigate to website
        print("Loading page...")
        driver.get("https://www.thegradcafe.com/survey")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        #5 Wait for survey results
        time.sleep(2)

        # Grab dynamic HTML directly from Selenium 
        html_content = driver.page_source

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the main table element
        table = soup.find("table")

        results = []

        if table:
            # Find all table rows within the table
            for row in table.find_all("tr"):
                # Find all table data cells inside the current row
                cells = row.find_all("td")

                # Skip empty or header rows
                if not cells:
                    continue

                school_info = cells[0].get_text(strip=True)

                if school_info:
                    results.append({"school": school_info})
        print(json.dumps(results[:5], indent=2))

    finally:
        driver.quit()
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

if __name__ == "__main__":
  main()