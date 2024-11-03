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
import time


def confirm_clickability(driver, element, timeout_long, timeout, data, attempts = 0, max_attempts = 2):
    """Crude function to confirm if an element is clickable. Ran in to many problems with partial loads and
    exceptions."""
    try:
        WebDriverWait(driver, timeout_long).until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//*[contains(@class, 'm-9814e45f mantine-Overlay-root')]")))

        for i in range(2):
            WebDriverWait(driver, timeout_long).until(
                EC.element_to_be_clickable(element))

            time.sleep(timeout)

        return

    except Exception as e:
        print('Function confirm_clickability entering next iteration', f'Exception: {e}')
        if attempts < max_attempts:
            try:
                driver.refresh()
                time.sleep(timeout)
                confirm_clickability(driver, element, timeout_long, timeout, attempts + 1, max_attempts) # Recursive call with incremented attempt count

            except Exception as e:
                print('Failure point: confirm_clickability', f'Exception: {e}')

        else:
            print('Failure point: confirm_clickability', 'max attempts reached')
            handle_failure(driver, data)


def select_lists(driver, timeout, lists):
    """Gets available lists and filters them according to user input."""
    # Go to 'Lists' page
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, "//*[@href='/lists']"))).click()

    # Scrape the webpage

    # Once page is loaded, find the list parent div
    list_parent_element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(
        (By.XPATH, "//*[contains(@class, 'side-panel__content screen-shell-aside__content')]")))

    # Get all anchor links
    anchor_element_list = list_parent_element.find_elements(By.TAG_NAME, "a")

    # Scrape selected lists if provided
    if lists:
        # Create a new list to hold the filtered elements
        filtered_anchor_list = []

        # Narrow list to specified names
        for anchor_element in anchor_element_list:
            if anchor_element.text.strip() in lists:  # Assuming 'lists' is a list or set of valid names
                filtered_anchor_list.append(anchor_element)

        return filtered_anchor_list

    else:
        return anchor_element_list


def login(driver, url, username, password, timeout):
    """Logs in to webpage with given credentials."""
    driver.get(url)  # Load the page

    # Log in to the first page

    # Find and enter username
    username_element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.ID, 'username')))
    username_element.send_keys(username)  # send username to input

    driver.find_element(By.XPATH, "//*[@type='submit']").click()  # Click the submit button

    # print("First Page Loaded.")

    # Log in to the second page

    # Find and enter password
    password_element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.ID, 'password')))

    password_element.send_keys(password)

    # Click the submit button
    driver.find_element(By.XPATH, "//*[@type='submit']").click()


def close_popups(driver, timeout):
    """Clears pop-ups from webpage."""
    WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='close banner']"))).click()  # Close banner

    close_button_list = driver.find_elements(By.ID, "closeModalBtn")  # Find button to close survey pop up

    # Click two close buttons
    for close_button in close_button_list:
        driver.execute_script("arguments[0].click();",
                              close_button)  # Force click using JavaScript (idk why but it works)

def get_athlete_list(driver, timeout, timeout_long, data):
    """Retrieves list of elements containing athlete information."""
    check_empty = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.subheading.subheading--small.result-count')))

    confirm_clickability(driver, check_empty, timeout_long, timeout, data)

    # Need to protect against empty lists
    check_empty = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.subheading.subheading--small.result-count'))).text

    if check_empty == 'No matching results':
        return []

    athlete_parent_element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "table__body")))

    confirm_clickability(driver, athlete_parent_element, timeout_long, timeout, data)

    # Get list of all athlete names
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.TAG_NAME, "tr")))

    return athlete_parent_element.find_elements(By.TAG_NAME, "tr")


def loop_athletes(driver, timeout, list_title, data):
    """Loops through list of athlete elements and adds their information to database."""
    athlete_parent_element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "table__body")))

    athlete_element_list = athlete_parent_element.find_elements(By.TAG_NAME, "tr")

    print('List: ', list_title, 'Athlete len: ', len(athlete_element_list))

    # Loop over each athlete
    for athlete_element in athlete_element_list:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(athlete_element)).click()

        name_element = WebDriverWait(athlete_element, timeout).until(EC.element_to_be_clickable((
            By.XPATH,
            "//*[contains(@class, 'focus-ring--active athlete-profile-contact__header--title')]")))

        try:
            number_element = athlete_element.find_element(By.XPATH, "//*[contains(@aria-label, 'Phone')]")
            number_value = number_element.text
        except NoSuchElementException:
            number_value = 'None'

        try:
            address_element = athlete_element.find_element(By.XPATH, "//*[contains(@aria-label, 'Address')]")
            address_value = address_element.text
        except NoSuchElementException:
            address_value = 'None'

        entry = {
            'Name': name_element.text,
            'Number': number_value,
            'Address': address_value,
            'List': list_title
        }

        # Append data to list
        data.append(entry)

        driver.find_element(By.XPATH, "//*[@aria-label='Close Athlete Profile']").click()  # Close athlete profile


def save_data(data):
    """Saves athlete data to user's Downloads folder."""
    # Create a DataFrame from the list of dictionaries to simplify excelification
    df = pd.DataFrame(data)

    timestamp = datetime.datetime.now().strftime("%m_%d_%Y")
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    excel_file_path = os.path.join(downloads_folder, f'athlete_data_{timestamp}.xlsx')

    # Write DataFrame to an Excel file
    df.to_excel(excel_file_path, index=False, engine='openpyxl')

def handle_failure(driver, data):
    """Saves athlete data and exits webdriver."""

    save_data(data)
    driver.quit()


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
    timeout = 10
    timeout_long = 30

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
        login(driver, url, username, password, timeout)

        #print("Logged in")

        close_popups(driver, timeout)

        #print("Closed Surveys.")

        anchor_element_list = select_lists(driver, timeout, lists)

        anchor_element = anchor_element_list[0]

        # Loop over each list
        for i in range(len(anchor_element_list)):
            list_title = anchor_element.text  # Prints list title

            #print('List Title: ', list_title)

            confirm_clickability(driver, anchor_element, timeout_long, timeout, data)

            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(anchor_element)).click()

            confirm_clickability(driver, anchor_element, timeout_long, timeout, data)

            athlete_element_list = get_athlete_list(driver, timeout, timeout_long, data)

            if not athlete_element_list:
                driver.refresh()
                athlete_element_list = get_athlete_list(driver, timeout, timeout_long, data)
                anchor_element_list = select_lists(driver, timeout, lists)
                anchor_element = anchor_element_list[i + 1]

                if not athlete_element_list:
                    print('No athletes found. Moving on')
                    anchor_element = anchor_element_list[i+1]
                    continue

            elif len(athlete_element_list) >= 100:
                page_parent_element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "pagination-container")))
                page_element_list = page_parent_element.find_elements(By.XPATH, "//*[contains(@class, 'pagination-item')]")
                #print(len(page_element_list))

                # Get rid of arrows
                page_element_list.pop(0)
                page_element_list.pop(-1)

                for page_element in page_element_list:
                    button = page_element.find_element(By.TAG_NAME, "button")

                    confirm_clickability(driver, page_element, timeout_long, timeout, data)

                    WebDriverWait(driver, timeout_long).until(EC.element_to_be_clickable(button)).click()

                    athlete_parent_element = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "table__body")))

                    confirm_clickability(driver, athlete_parent_element, timeout_long, timeout, data)

                    loop_athletes(driver, timeout, list_title, data) # Loop over each athlete
                    anchor_element = anchor_element_list[i + 1]

            else:
                # Loop over each athlete
                loop_athletes(driver, timeout, list_title, data)  # Loop over each athlete
                anchor_element = anchor_element_list[i + 1]

        driver.quit()
        save_data(data)

        return 'success'

    except Exception as e:
        print(e)
        driver.quit()
        save_data(data)
        return 'failure'
