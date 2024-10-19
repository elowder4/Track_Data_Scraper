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
    """Scrapes nscasports webpage by logging in with a given username and password.
    username: username for login.
    password: password for login.
    lists: lists to loop over.
    output: returns string success or failure"""

    # Store athlete data
    data = []

    # Set URL
    url = 'https://coach-x.ncsasports.org/'

    # Load environment variables
    load_dotenv()

    # Set Timout and Wait Time
    timeout = 20

    # Set Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.headless = True
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    # Use a random user agent
    ua = UserAgent().random
    chrome_options.add_argument(f'user-agent={ua}')

    # Initialize the WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
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

        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='close banner']"))).click()  # Close banner

        close_button_list = driver.find_elements(By.ID, "closeModalBtn")  # Find button to close survey pop up

        # Click two close buttons
        for close_button in close_button_list:
            driver.execute_script("arguments[0].click();", close_button) # Force click using JavaScript (idk why but it works)

        #print("Closed Surveys.")

        # Go to 'Lists' page
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[@href='/lists']"))).click()

        # Scrape the webpage

        # Once page is loaded, find the list parent div
        list_parent_element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'side-panel__content screen-shell-aside__content')]")))

        # Get all anchor links
        anchor_element_list = list_parent_element.find_elements(By.TAG_NAME, "a")

        # Scrape selected lists if provided
        if lists:
            # Create a new list to hold the filtered elements
            filtered_anchor_list = []

            # Narrow list to specified names
            for anchor_element in anchor_element_list:
                if anchor_element.text in lists:  # Assuming 'lists' is a list or set of valid names
                    filtered_anchor_list.append(anchor_element)

            anchor_element_list = filtered_anchor_list

        anchor_element = anchor_element_list[0]  # Used in loop

        num_loops = len(anchor_element_list)

        # Loop over each list using len because elements must be refreshed each iteration
        for i in range(num_loops):
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(anchor_element)).click()  # Clicks on list

            # Wait for blurry cover to go away
            WebDriverWait(driver, timeout).until(
                EC.invisibility_of_element_located((By.XPATH, "//*[contains(@class, 'm-9814e45f mantine-Overlay-root')]")))
            #print("Overlay is gone")
            # could try reloading page here if overlay doesnt go bye bye

            #print("List Title: ", anchor_element.text)  # Prints list title

            athlete_parent_element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "table__body")))

            # Get list of all athlete names
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.TAG_NAME, "tr")))
            athlete_element_list = athlete_parent_element.find_elements(By.TAG_NAME, "tr")

            #print(len(athlete_element_list))

            # Loop over each athlete
            for athlete_element in athlete_element_list:
                WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(athlete_element)).click()

                name_element = WebDriverWait(athlete_element, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'focus-ring--active athlete-profile-contact__header--title')]")))

                number_element = athlete_element.find_element(By.XPATH, "//*[contains(@aria-label, 'Phone')]")

                try:
                    address_element = athlete_element.find_element(By.XPATH, "//*[contains(@aria-label, 'Address')]")
                    entry = {
                        'Name': name_element.text,
                        'Number': number_element.text,
                        'Address': address_element.text
                    }
                except NoSuchElementException:
                    entry = {
                        'Name': name_element.text,
                        'Number': number_element.text,
                        'Address': 'None'
                    }

                # Append data to list
                data.append(entry)

                driver.find_element(By.XPATH, "//*[@aria-label='Close Athlete Profile']").click()  # Close athlete profile

            anchor_element_list.pop(0)  # Get rid of looped over list
            if anchor_element_list:
                anchor_element = anchor_element_list[0]  # Update to next list

        # Create a DataFrame from the list of dictionaries to simplify excelification
        df = pd.DataFrame(data)

        timestamp = datetime.datetime.now().strftime("%Y_%m_%d")
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        excel_file_path = os.path.join(downloads_folder, f'athlete_data_{timestamp}.xlsx')

        # Write DataFrame to an Excel file
        df.to_excel(excel_file_path, index=False, engine='openpyxl')

        driver.quit()  # End session

        return 'success'

    except Exception as e:
        print(e)
        driver.quit()
        return 'failure'
