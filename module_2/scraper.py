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
admissions_results = soup.find_all("tbody", class_="tw-divide-y tw-divide-gray-200 tw-bg-white")
for admission_result in admissions_results:
    print(admission_result, end="\n" * 2)
    text = admission_result.get_text(strip=True)
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