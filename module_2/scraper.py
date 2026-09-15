# Create list of parameters to search website with using mechanical soup
# Create for loop to query webiste
# Parse data using BeautifulSoup
# Save parsed data as JSON file

import time
import requests
from bs4 import BeautifulSoup
import mechanicalsoup

URL = "https://www.thegradcafe.com/survey"
page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
program_names = soup.find_all("div", class_="tw-text-gray-900")
for program_name in program_names:
    text = program_name.get_text(strip=True)
    if text:
        print(text)


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