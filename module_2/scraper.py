# Create list of parameters to search website with using mechanical soup
# Create for loop to query webiste
# Parse data using BeautifulSoup
# Save parsed data as JSON file

import time
import mechanicalsoup

# Function for scraping website
def scrape():
    browser = mechanicalsoup.Browser()
    page = browser.get("https://www.thegradcafe.com/survey")
    return

# Function to save scraped data
def save_data():
    pass

################################################################################

if __name__ == "__main__":
  results = scrape()