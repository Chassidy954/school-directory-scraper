import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time

def search_districts_and_click_link_on_cde(districts_file, district_column_name='District'):
    """
    Automates searching for district names on the California School Directory website,
    and then clicks the matching hyperlink for each search result.

    Args:
        districts_file (str): Path to the file containing district names (e.g., 'districts_with_contacts.csv').
        district_column_name (str): The name of the column in the file that contains district names.
    """

    # --- Configuration ---
    CDE_URL = "https://www.cde.ca.gov/SchoolDirectory/"
    SEARCH_BAR_ID = "AllSearchField"

    # --- CORRECTED SELECTOR based on your HTML screenshot! ---
    # This selects <a> tags that are inside a <td>, which is inside a <tr>,
    # which is inside a <tbody>, which is inside a table with classes 'table' and 'table-bordered'.
    DISTRICT_LINK_SELECTOR = "table.table-bordered tbody tr td a"

    # --- Geckodriver (for Firefox) Configuration ---
    DRIVER_PATH = None # Set to None if geckodriver is in your system's PATH

    print(f"Loading district names from '{districts_file}'...")
    try:
        df = pd.read_csv(districts_file)
    except Exception:
        try:
            df = pd.read_excel(districts_file)
        except Exception as e:
            print(f"Error: Could not read '{districts_file}'. Make sure it's a valid CSV or Excel file.")
            print(e)
            return

    if district_column_name not in df.columns:
        print(f"Error: Column '{district_column_name}' not found in the file.")
        print(f"Available columns: {df.columns.tolist()}")
        return

    district_names = df[district_column_name].dropna().unique().tolist()
    if not district_names:
        print("No district names found in the specified column.")
        return

    print(f"Found {len(district_names)} unique district names to search.")
    print("Initializing web browser (Firefox with Geckodriver)...")

    driver = None
    try:
        if DRIVER_PATH:
            from selenium.webdriver.firefox.service import Service
            service = Service(executable_path=DRIVER_PATH)
            driver = webdriver.Firefox(service=service)
        else:
            driver = webdriver.Firefox()

        driver.maximize_window()
        driver.get(CDE_URL)

        wait = WebDriverWait(driver, 20)

        print("Browser ready. Starting searches and link clicks...")

        for i, district_name in enumerate(district_names):
            print(f"\n--- ({i+1}/{len(district_names)}) Processing: '{district_name}' ---")
            try:
                # Re-locate the search bar in each iteration to avoid StaleElementReferenceException
                search_bar = wait.until(EC.presence_of_element_located((By.ID, SEARCH_BAR_ID)))

                # Clear any previous text
                search_bar.send_keys(Keys.CONTROL + "a")
                search_bar.send_keys(Keys.DELETE)
                time.sleep(0.5)

                # Enter the district name
                search_bar.send_keys(district_name)
                search_bar.send_keys(Keys.RETURN)

                # --- Wait for the search results to appear using the new selector ---
                print(f"Waiting for search results to be clickable using selector: '{DISTRICT_LINK_SELECTOR}'...")
                try:
                    # Wait for at least one search result link to be clickable
                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, DISTRICT_LINK_SELECTOR)))
                    time.sleep(1) # Give a little extra time for all results to render
                except TimeoutException:
                    print(f"Timeout: Search results for '{district_name}' did not appear in time using selector '{DISTRICT_LINK_SELECTOR}'.")
                    print("This likely means the selector is still incorrect, or the results load very slowly.")
                    driver.get(CDE_URL) # Go back to the initial URL to reset
                    continue # Skip to the next district

                # --- Find and Click the Matching Hyperlink ---
                found_link = False
                try:
                    # Get all potential district links from the search results
                    # IMPORTANT: Use find_elements here, as there could be multiple links,
                    # and we need to iterate to find the one with the correct text.
                    result_links = driver.find_elements(By.CSS_SELECTOR, DISTRICT_LINK_SELECTOR)

                    if not result_links:
                        print(f"Warning: No elements found with selector '{DISTRICT_LINK_SELECTOR}' for '{district_name}' after search.")
                        print("This indicates the selector might be correct, but no links were found.")

                    for link in result_links:
                        # Ensure the link element is visible and contains the district name
                        if link.is_displayed() and district_name.lower() in link.text.lower():
                            print(f"Found matching link: '{link.text}'")
                            link.click()
                            found_link = True
                            break # Exit loop once the correct link is found and clicked

                    if found_link:
                        print(f"Clicked link for '{district_name}'. Now on district page.")
                        time.sleep(5) # Wait on the district page to observe

                        # --- Navigate back to the main search page ---
                        print("Navigating back to the search page...")
                        driver.back()
                        # After going back, we wait for the search bar to be present again
                        wait.until(EC.presence_of_element_located((By.ID, SEARCH_BAR_ID)))
                        time.sleep(2) # Give it a moment to fully load the previous state
                    else:
                        print(f"No exact matching link found for '{district_name}' on the results page.")
                        print("The search might have yielded no results, or the text didn't exactly match a link.")
                        # If no link is found, we should still go back to the original search page
                        driver.get(CDE_URL)
                        wait.until(EC.presence_of_element_located((By.ID, SEARCH_BAR_ID)))
                        time.sleep(2)

                except NoSuchElementException:
                    print(f"Error: No elements found by selector '{DISTRICT_LINK_SELECTOR}' after search for '{district_name}'.")
                    print("This should have been caught by the TimeoutException, but could occur if elements disappear quickly.")
                    driver.get(CDE_URL)
                    continue
                except StaleElementReferenceException:
                    print(f"Stale element encountered when trying to find/click link for '{district_name}'. This shouldn't happen with the new selector, but resetting.")
                    driver.get(CDE_URL)
                    continue
                except Exception as link_error:
                    print(f"Unexpected error when processing link for '{district_name}': {link_error}")
                    driver.get(CDE_URL)
                    continue

            except Exception as e:
                print(f"An unexpected error occurred during search or initial page interaction for '{district_name}': {e}")
                # Attempt to go back to original page to recover for next search
                try:
                    driver.get(CDE_URL)
                    wait.until(EC.presence_of_element_located((By.ID, SEARCH_BAR_ID)))
                except:
                    pass # Ignore errors during emergency navigation
                continue

        print("\nAll district searches and link clicks completed.")

    except Exception as e:
        print(f"An error occurred during browser automation: {e}")
        print("Please ensure you have Geckodriver installed and its path is configured correctly.")
        print("For Firefox, download Geckodriver from: https://github.com/mozilla/geckodriver/releases")
        print("Make sure the Geckodriver version is compatible with your Firefox browser version.")

    finally:
        if driver:
            print("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    test_file_name = 'NoCohort.xlsx'
    try:
        pd.DataFrame({
            'District': ['Manteca Unified', 'Anaheim Union High', 'Los Angeles Unified', 'San Francisco Unified School District'],
            'Contact': ['John Doe', 'Jane Smith', 'Peter Jones', 'Alice Brown']
        }).to_excel(test_file_name, index=False)
        print(f"Created a sample '{test_file_name}' for testing.")
    except Exception as e:
        print(f"Could not create dummy file: {e}. Please ensure you have pandas installed and openpyxl (pip install openpyxl).")

    search_districts_and_click_link_on_cde(test_file_name, district_column_name='District')