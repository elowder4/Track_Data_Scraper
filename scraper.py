import requests
import json
import os
import csv
import time
import sys
import urllib.request
from datetime import date
from dotenv import load_dotenv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from json import JSONDecoder
from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service

def wait_for_load(timeout):
    """Helper function that waits for page to load with a timeout.
    return: None"""
    # Wait until the page has completely loaded by waiting for the document ready state
    wait = WebDriverWait(driver, 10)
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

# Username and password for website - hardcoded for now
username = ''
password = ''

# Set URL
url = 'https://coach-x.ncsasports.org/'

# Load environment variables
load_dotenv()

# Set Timout and Wait Time
timeout = 10

# Set Chrome options
chrome_options = Options()
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.headless = True
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)

# Use a random user agent
ua = UserAgent()
userAgent = ua.random
chrome_options.add_argument(f'user-agent={userAgent}')

# Initialize the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

driver.get(url)  # Load the page

# Log in to the first page
try:
    # Find and enter username
    Username = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.ID, 'username')))
    Username.send_keys(username)  # send username to input

    driver.find_element(By.XPATH, "//*[@type='submit']").click()  # Click the submit button

except:
    print("First Page Failed to Load. Please contact Ethan or Joel.")
    sys.exit()  # Terminate the script execution

# Log in to the second page
try:
    # Find and enter password
    Password = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.ID, 'password')))

    Password.send_keys(password)

    # Click the submit button
    driver.find_element(By.XPATH, "//*[@type='submit']").click()

except:
    print("Second Page Failed to Load. Please contact Ethan or Joel.")
    sys.exit()  # Terminate the script execution

WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='close banner']"))).click()

buttonList = driver.find_elements(By.ID, "closeModalBtn")

# Click two close buttons
for button in buttonList:
    driver.execute_script("arguments[0].click();", button) # Force click using JavaScript (idk why)

print("Failed to Close Surveys. Please contact Ethan or Joel.")

# Go to 'Lists' page
WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[@href='/lists']"))).click()

# Scrape the webpage
try:
    # Once page is loaded, find the list parent div
    element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'side-panel__content screen-shell-aside__content')]")))

    # Get all list links with the specified class
    webEleList = element.find_elements(By.TAG_NAME, "a")

    # Loop over each list
    for webElement in webEleList:
        print("List Title: ", webElement.text)  # Prints list title

        webElement.click()  # Clicks on list

        parentElem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CLASS_NAME, "table__body")))

        # Get list of all athlete names
        athleteList = parentElem.find_elements(By.TAG_NAME, "tr")

        # Loop over each athlete
        for athlete in athleteList:
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(athlete)).click()

            nameElem = WebDriverWait(athlete, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'focus-ring--active athlete-profile-contact__header--title')]")))

            print(nameElem.text)

            numberElem = athlete.find_element(By.XPATH, "//*[contains(@aria-label, 'Phone')]")

            print(numberElem.text)

            try:
                addressElem = athlete.find_element(By.XPATH, "//*[contains(@aria-label, 'Address')]")
                print(addressElem.text)
            except NoSuchElementException:
                print('None')

            driver.find_element(By.XPATH, "//*[@aria-label='Close Athlete Profile']").click()

except NoSuchElementException:
    print("Could not find the div element on the page")

finally:
    # Close the browser
    driver.quit()
