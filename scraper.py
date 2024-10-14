import os
import datetime
from dotenv import load_dotenv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service
import pandas as pd


def scrape(username: str, password: str, lists: [str]) -> str:
    '''Scrapes nscasports webpage by logging in with a given username and password.
    username: username for login.
    password: password for login.
    lists: lists to loop over.
    output: returns string sucess or failure'''

    # Store athlete data
    data = []

    # Set URL
    url = 'https://coach-x.ncsasports.org/'

    try:
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

        # Find and enter username
        username_element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.ID, 'username')))
        username_element.send_keys(username)  # send username to input

        driver.find_element(By.XPATH, "//*[@type='submit']").click()  # Click the submit button

        #print("First Page Loaded.")

        # Log in to the second page

        # Find and enter password
        password_element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.ID, 'password')))

        password_element.send_keys(password)

        # Click the submit button
        driver.find_element(By.XPATH, "//*[@type='submit']").click()

        #print("Second Page Loaded.")

        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='close banner']"))).click()

        buttonList = driver.find_elements(By.ID, "closeModalBtn")

        # Click two close buttons
        for button in buttonList:
            driver.execute_script("arguments[0].click();", button) # Force click using JavaScript (idk why)

        #print("Closed Surveys.")

        # Go to 'Lists' page
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[@href='/lists']"))).click()

        # Scrape the webpage

        # Once page is loaded, find the list parent div
        element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'side-panel__content screen-shell-aside__content')]")))

        # Get all anchor links
        webEleList = element.find_elements(By.TAG_NAME, "a")

        # Create a new list to hold the filtered elements
        filteredList = []

        # Narrow list to specified names
        for ele in webEleList:
            if ele.text in lists:  # Assuming 'lists' is a list or set of valid names
                filteredList.append(ele)

        # If you want to update 'webEleList' to only include the specified names
        webEleList = filteredList

        # Loop over each list
        for webElement in webEleList:
            #print("List Title: ", webElement.text)  # Prints list title

            parentElem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CLASS_NAME, "table__body")))

            webElement.click()  # Clicks on list

            # Get list of all athlete names
            athleteList = parentElem.find_elements(By.TAG_NAME, "tr")

            # Loop over each athlete
            for athlete in athleteList:
                WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(athlete)).click()

                nameElem = WebDriverWait(athlete, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'focus-ring--active athlete-profile-contact__header--title')]")))

                numberElem = athlete.find_element(By.XPATH, "//*[contains(@aria-label, 'Phone')]")

                try:
                    addressElem = athlete.find_element(By.XPATH, "//*[contains(@aria-label, 'Address')]")
                    entry = {
                        'Name': nameElem.text,
                        'Number': numberElem.text,
                        'Address': addressElem.text
                    }
                except NoSuchElementException:
                    entry = {
                        'Name': nameElem.text,
                        'Number': numberElem.text,
                        'Address': 'None'
                    }

                # Append data to list
                data.append(entry)

                driver.find_element(By.XPATH, "//*[@aria-label='Close Athlete Profile']").click()

        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(data)

        timestamp = datetime.datetime.now().strftime("%Y_%m_%d")
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        excel_file_path = os.path.join(downloads_folder, f'athlete_data_{timestamp}.xlsx')

        # Write DataFrame to an Excel file
        df.to_excel(excel_file_path, index=False, engine='openpyxl')

        return 'success'

    except:
        return 'failure'
