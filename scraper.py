from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from dotenv import load_dotenv
from selenium import webdriver
import pandas as pd
import datetime
import time
import os


class Scraper:
    def __init__(self, username, password, lists, timeout = 20):
        """Constructor function for Scraper class."""

        # Set URL
        self.url = 'https://coach-x.ncsasports.org/'

        # Load environment variables
        load_dotenv()

        # Set Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.headless = True
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless")  # Make Chrome run in background (no window)
        chrome_options.add_argument("--no-sandbox")
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)

        # Use a random user agent
        ua = UserAgent().random
        chrome_options.add_argument(f'user-agent={ua}')

        data = []

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.username = username
        self.password = password
        self.lists = lists
        self.timeout = timeout
        self.data = data
        
        
    def parse_element_info(self, element_info):
        """Helper function to parse dictionary that holds element information."""
        
        if 'index' in element_info and element_info['index'] is not None:
            index = element_info['index']

        else:
            index = None
        
        if index is not None:
            if element_info['selector'] == 'lists':
                WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.XPATH, element_info['information'])))
                elements = self.select_lists()
                element = elements[index]
            elif element_info['selector'] == 'button':
                page_parent_element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.CLASS_NAME, "pagination-container")))
                page_element_list = page_parent_element.find_elements(By.XPATH,"//*[contains(@class, 'pagination-item')]")
                # Get rid of arrows
                page_element_list.pop(0)
                page_element_list.pop(-1)
                element = page_element_list[index].find_element(By.TAG_NAME, "button")
            elif element_info['selector'] == 'xpath':
                WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.XPATH, element_info['information'])))
                elements = self.driver.find_elements(By.XPATH, element_info['information'])
                element = elements[index]
            elif element_info['selector'] == 'class':
                WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.CLASS_NAME, element_info['information'])))
                elements = self.driver.find_elements(By.CLASS_NAME, element_info['information'])
                element = elements[index]
            elif element_info['selector'] == 'css':
                WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.CSS_SELECTOR, element_info['information'])))
                elements = self.driver.find_elements(By.CSS_SELECTOR, element_info['information'])
                element = elements[index]
            else:
                WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.TAG_NAME, element_info['information'])))
                elements = self.driver.find_elements(By.TAG_NAME, element_info['information'])
                element = elements[index]
        
        else:
            if element_info['selector'] == 'xpath':
                element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.XPATH, element_info['information'])))
            elif element_info['selector'] == 'class':
                element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.CLASS_NAME, element_info['information'])))
            elif element_info['selector'] == 'css':
                element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.CSS_SELECTOR, element_info['information'])))
            elif element_info['selector'] == 'tag':
                element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.TAG_NAME, element_info['information'])))
            else:
                element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.ID, element_info['information'])))
            
        return element


    def confirm_clickability(self, element_info, attempts = 0, max_attempts = 2):
        """Crude function to confirm if an element is clickable. Ran in to many problems with partial loads and
        exceptions."""
        
        element = self.parse_element_info(element_info)
        
        try:
            WebDriverWait(self.driver, self.timeout).until(ec.invisibility_of_element_located((By.XPATH, "//*[contains(@class, 'm-9814e45f mantine-Overlay-root')]")))
    
            for i in range(2):
                WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable(element))
                time.sleep(self.timeout/2)
    
            return True
    
        except Exception as e:
            print('Function confirm_clickability entering next iteration', f'Exception: {e}')
            if attempts < max_attempts:
                try:
                    self.driver.refresh()
                    time.sleep(self.timeout)
                    self.confirm_clickability(element_info, attempts + 1, max_attempts) # Recursive call with incremented attempt count
    
                except Exception as e:
                    print('Failure point: confirm_clickability', f'Exception: {e}')
    
            else:
                print('Failure point: confirm_clickability', 'max attempts reached')
                self.handle_failure()


    def select_lists(self):
        """Gets available self.lists and filters them according to user input."""
    
        if self.lists:
            # Clean and split the self.lists input
            clean_lists = [item.strip() for item in self.lists.split(',')]
            # print(loop_self.lists)
        else:
            clean_lists = []
    
        # Go to 'lists' page
        WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.XPATH, "//*[@href='/lists']"))).click()
    
        # Scrape the webpage
    
        # Once page is loaded, find the list parent div
        list_parent_element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable(
            (By.XPATH, "//*[contains(@class, 'side-panel__content screen-shell-aside__content')]")))
    
        # Get all anchor links
        anchor_element_list = list_parent_element.find_elements(By.TAG_NAME, "a")
    
        # Scrape selected self.lists if provided
        if clean_lists:
            # Create a new list to hold the filtered elements
            filtered_anchor_list = []
    
            # Narrow list to specified names
            for anchor_element in anchor_element_list:
                if anchor_element.text.strip() in clean_lists:  # Assuming 'self.lists' is a list or set of valid names
                    filtered_anchor_list.append(anchor_element)
    
            return filtered_anchor_list
    
        else:
            return anchor_element_list


    def login(self):
        """Logs in to webpage with given credentials."""

        self.driver.get(self.url)  # Load the page

        # Log in to the first page

        # Find and enter username
        username_element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.ID, 'username')))
        username_element.send_keys(self.username)  # send username to input

        self.driver.find_element(By.XPATH, "//*[@type='submit']").click()  # Click the submit button

        # print("First Page Loaded.")

        # Log in to the second page

        # Find and enter password
        password_element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.ID, 'password')))

        password_element.send_keys(self.password)

        # Click the submit button
        self.driver.find_element(By.XPATH, "//*[@type='submit']").click()


    def close_popups(self):
        """Clears pop-ups from webpage."""

        WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.XPATH, "//*[@aria-label='close banner']"))).click()  # Close banner

        close_button_list = self.driver.find_elements(By.ID, "closeModalBtn")  # Find button to close survey pop up

        # Click two close buttons
        for close_button in close_button_list:
            self.driver.execute_script("arguments[0].click();",close_button)  # Force click using JavaScript (hey, it works)


    def get_athlete_list(self):
        """Retrieves list of elements containing athlete information."""

        self.confirm_clickability({'selector':'css', 'information':'.subheading.subheading--small.result-count'})

        # Need to protect against empty self.lists
        check_empty = WebDriverWait(self.driver, self.timeout).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, '.subheading.subheading--small.result-count'))).text

        if check_empty == 'No matching results':
            return []

        athlete_parent_element = WebDriverWait(self.driver, self.timeout).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "table__body")))

        self.confirm_clickability({'selector':'class','information':'table__body'})

        # Get list of all athlete names
        WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.TAG_NAME, "tr")))

        return athlete_parent_element.find_elements(By.TAG_NAME, "tr")


    def loop_athletes(self, list_title):
        """Loops through list of athlete elements and adds their information to self.database."""

        athlete_parent_element = WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable((By.CLASS_NAME, "table__body")))

        athlete_element_list = athlete_parent_element.find_elements(By.TAG_NAME, "tr")

        #print('List: ', list_title, 'Athlete len: ', len(athlete_element_list))

        # Loop over each athlete
        for athlete_element in athlete_element_list:
            WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable(athlete_element)).click()

            name_element = WebDriverWait(athlete_element, self.timeout).until(ec.element_to_be_clickable((
                By.XPATH, "//*[contains(@class, 'focus-ring--active athlete-profile-contact__header--title')]")))

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

            # Append self.data to list
            self.data.append(entry)

            self.driver.find_element(By.XPATH, "//*[@aria-label='Close Athlete Profile']").click()  # Close athlete profile


    def save_data(self):
        """Saves athlete self.data to user's Downloads folder."""

        # Create a dataFrame from the list of athlete information to simplify excelification
        df = pd.DataFrame(self.data)

        timestamp = datetime.datetime.now().strftime("%m_%d_%Y")
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        excel_file_path = os.path.join(downloads_folder, f'athlete_data_{timestamp}.xlsx')

        # Write self.dataFrame to an Excel file
        df.to_excel(excel_file_path, index=False, engine='openpyxl')


    def handle_failure(self):
        """Saves athlete self.data and exits self.driver."""

        self.save_data()
        self.driver.quit()


    def scrape(self) -> str:
        """Scrapes nscasports webpage by logging in with a given username and password.
        username: username for login.
        password: password for login.
        self.lists: self.lists to loop over.
        output: returns string success or failure"""

        try:
            self.login()

            #print("Logged in")

            self.close_popups()

            #print("Closed Surveys.")

            anchor_element_list = self.select_lists()

            if self.confirm_clickability({'selector': 'lists','information': "//*[contains(@class, 'side-panel__content screen-shell-aside__content')]",'index': 0}):
                pass
            else:
                anchor_element_list = self.select_lists()  # Update lists to account for reloads

            #print(len(anchor_element_list))

            # Loop over each list
            for i in range(len(anchor_element_list)):
                anchor_element = anchor_element_list[i]
                list_title = anchor_element.text

                #print(f'List Title {i}: ', list_title)

                WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable(anchor_element)).click()

                athlete_element_list = self.get_athlete_list()

                if not athlete_element_list:
                    self.driver.refresh()
                    time.sleep(self.timeout)

                    athlete_element_list = self.get_athlete_list()
                    anchor_element_list = self.select_lists()

                    if not athlete_element_list:
                        #print('No athletes found. Moving on')
                        if i == (len(anchor_element_list) - 1):
                            pass
                        else:
                            continue

                elif len(athlete_element_list) >= 100:
                    page_parent_element = WebDriverWait(self.driver, self.timeout).until(
                        ec.element_to_be_clickable((By.CLASS_NAME, "pagination-container")))
                    page_element_list = page_parent_element.find_elements(By.XPATH, "//*[contains(@class, 'pagination-item')]")
                    #print(len(page_element_list))

                    # Get rid of arrows
                    page_element_list.pop(0)
                    page_element_list.pop(-1)

                    j = 0 # Index for confirm_clickability

                    for page_element in page_element_list:
                        button = page_element.find_element(By.TAG_NAME, "button")

                        if self.confirm_clickability({'selector':'button','information':'button','index':j}):
                            pass
                        else:
                            page_parent_element = WebDriverWait(self.driver, self.timeout).until(
                                ec.element_to_be_clickable((By.CLASS_NAME, "pagination-container")))
                            page_element_list = page_parent_element.find_elements(By.XPATH,"//*[contains(@class, 'pagination-item')]")
                            #print(len(page_element_list))

                            # Get rid of arrows
                            page_element_list.pop(0)
                            page_element_list.pop(-1)

                        WebDriverWait(self.driver, self.timeout).until(ec.element_to_be_clickable(button)).click()

                        if self.confirm_clickability({'selector':'class','information':'table__body'}):
                            pass
                        else:
                            page_parent_element = WebDriverWait(self.driver, self.timeout).until(
                                ec.element_to_be_clickable((By.CLASS_NAME, "pagination-container")))
                            page_element_list = page_parent_element.find_elements(By.XPATH,
                                                                                  "//*[contains(@class, 'pagination-item')]")
                            #print(len(page_element_list))

                            # Get rid of arrows
                            page_element_list.pop(0)
                            page_element_list.pop(-1)

                        self.loop_athletes(list_title) # Loop over each athlete

                        if i == (len(anchor_element_list) - 1):
                            pass
                        else:
                            continue

                        j += 1

                else:
                    # Loop over each athlete
                    self.loop_athletes(list_title)  # Loop over each athlete

                    if i == (len(anchor_element_list) - 1):
                        pass
                    else:
                        continue

            self.driver.quit()
            self.save_data()

            return 'success'

        except Exception as e:
            print('Ultimate Failure: ', e)
            self.driver.quit()
            self.save_data()
            return 'failure'
    