from selenium import webdriver
from selenium.webdriver import ChromeOptions

options = ChromeOptions()
options.add_argument("--headless=new")

driver = webdriver.Chrome(options=options)
driver.get("https://www.oxylabs.io/")
print(driver.page_source)
driver.quit()