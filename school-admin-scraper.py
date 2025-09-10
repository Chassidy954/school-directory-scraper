import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time
import re
import os

# --- Generic Web Scraper Configuration ---
# To use this script for a different website, only update this dictionary.
WEBSITE_CONFIG = {
    'url': "https://www.cde.ca.gov/SchoolDirectory/",
    'search_bar_id': "AllSearchField",
    'search_results_link_selector': "table.table-bordered tbody tr td a",
    'detail_page_name_selector': "h1.page-title",
    'contact_data_xpaths': {
        'Superintendent': "//th[@class='details-field-label' and contains(text(), 'Superintendent')]/following-sibling::td",
        'Chief Business Official': "//th[@class='details-field-label' and contains(text(), 'Chief Business Official')]/following-sibling::td"
    },
    'input_column': 'District Name',
    'output_columns': {
        'name': 'Contact Name',
        'job_title': 'Contact Job Title',
        'email': 'Contact Email',
        'phone': 'Contact Phone Number'
    }
}

def extract_contact_info(td_element):
    """
    Extracts name, phone, and email from a given td element.
    Returns a tuple (name, phone, email), with "N/A" for missing data.
    """
    name = "N/A"
    phone = "N/A"
    email = "N/A"

    full_text = td_element.text.strip()
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]

    if lines:
        name = lines[0]

    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', full_text)
    if phone_match:
        phone = phone_match.group(0)

    try:
        email_link = td_element.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
        email = email_link.get_attribute("href").replace("mailto:", "")
    except NoSuchElementException:
        pass
    except Exception as e:
        print(f"    Error extracting email: {e}")
        pass

    return name, phone, email

def clean_search_term(term):
    """
    Removes common trailing terms to improve search accuracy.
    """
    cleaned_name = term.strip()
    cleaned_name = re.sub(r'\s+school\s+district$', '', cleaned_name, flags=re.IGNORECASE).strip()
    cleaned_name = re.sub(r'\s+district$', '', cleaned_name, flags=re.IGNORECASE).strip()
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
    return cleaned_name

def run_scraper_with_config(config, input_file):
    """
    A reusable web scraping function that reads a list of items from an Excel file,
    searches for each item on a website, navigates to its detail page, scrapes
    specified contact information, and updates the original Excel file.
    
    Args:
        config (dict): A dictionary containing all website-specific selectors and URLs.
        input_file (str): Path to the Excel file containing the list of items to search.
    """
    print(f"Loading search terms from '{input_file}'...")
    try:
        df = pd.read_excel(input_file)
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found. Please ensure it exists.")
        return
    except Exception as e:
        print(f"Error: Could not read '{input_file}'. Make sure it's a valid Excel file and openpyxl is installed.")
        print(e)
        return

    if config['input_column'] not in df.columns:
        print(f"Error: Column '{config['input_column']}' not found in the file.")
        print(f"Available columns: {df.columns.tolist()}")
        return

    search_terms = df[config['input_column']].dropna().unique().tolist()
    if not search_terms:
        print("No search terms found in the specified column.")
        return

    print(f"Identified {len(search_terms)} unique terms to process.")
    
    driver = None
    processed_count = 0
    skipped_items = []
    scraped_records = []

    try:
        print("Initializing web browser...")
        driver = webdriver.Firefox()
        driver.maximize_window()
        print("Browser ready.")
    except Exception as e:
        print(f"\nCRITICAL ERROR: Failed to initialize web browser. Error: {e}")
        print("Please ensure you have the required browser driver (e.g., 'geckodriver' for Firefox) installed and its path is correctly configured in your system's PATH variable.")
        return
    
    try:
        print("Starting data extraction...")

        for i, original_term in enumerate(search_terms):
            print(f"\n--- ({i+1}/{len(search_terms)}) Processing: '{original_term}' ---")
            
            driver.get(config['url'])
            
            try:
                search_bar = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, config['search_bar_id']))
                )
            except TimeoutException:
                print("Failed to load initial search page. Aborting.")
                break
            
            search_bar.send_keys(Keys.CONTROL + "a")
            search_bar.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            search_term = clean_search_term(original_term)
            print(f"    Searching with cleaned term: '{search_term}'")
            
            search_bar.send_keys(search_term)
            search_bar.send_keys(Keys.RETURN)
            
            time.sleep(2)

            landed_on_detail_page = False
            try:
                page_name_element = driver.find_element(By.CSS_SELECTOR, config['detail_page_name_selector'])
                if search_term.lower() in page_name_element.text.lower():
                    print("    Directly landed on a matching detail page.")
                    landed_on_detail_page = True
            except NoSuchElementException:
                pass

            if not landed_on_detail_page:
                try:
                    link_found = False
                    result_links = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, config['search_results_link_selector']))
                    )
                    
                    for link in result_links:
                        if search_term.lower() in link.text.lower():
                            link.click()
                            link_found = True
                            break
                    if not link_found:
                        print(f"    No matching link found for '{original_term}'. Skipping.")
                        skipped_items.append(f"{original_term} (No matching link)")
                        continue
                    
                except (TimeoutException, NoSuchElementException):
                    print(f"    No search results for '{original_term}'. Skipping.")
                    skipped_items.append(f"{original_term} (No search results)")
                    continue

            print(f"    On detail page. Extracting data...")
            
            found_data = False
            for job_title, xpath in config['contact_data_xpaths'].items():
                try:
                    td_element = driver.find_element(By.XPATH, xpath)
                    name, phone, email = extract_contact_info(td_element)
                    
                    if name != "N/A":
                        found_data = True
                        record = {
                            config['input_column']: original_term,
                            config['output_columns']['name']: name,
                            config['output_columns']['job_title']: job_title,
                            config['output_columns']['email']: email,
                            config['output_columns']['phone']: phone,
                        }
                        scraped_records.append(record)
                        print(f"        Found: {job_title}, Name: '{name}'")
                    else:
                        print(f"        {job_title} info incomplete.")
                except NoSuchElementException:
                    print(f"        {job_title} section not found.")
                except Exception as e:
                    print(f"        Error for {job_title}: {e}")

            if found_data:
                processed_count += 1
            else:
                skipped_items.append(f"{original_term} (No contact data found)")
            
            time.sleep(2)
            
    except Exception as e:
        print(f"\nAN UNEXPECTED ERROR OCCURRED DURING SCRAPING: {e}")

    finally:
        if driver:
            print("Closing browser...")
            driver.quit()

        print("\nSaving updated Excel file...")
        if scraped_records:
            scraped_df = pd.DataFrame(scraped_records)
            merged_df = pd.merge(df, scraped_df, on=config['input_column'], how='left')
            try:
                merged_df.to_excel(input_file, index=False)
                print(f"Successfully updated '{input_file}'.")
            except Exception as e:
                print(f"Error saving file: {e}")
        else:
            print("No new data to save. The original file remains unchanged.")

        print("\n--- SCRAPING SUMMARY ---")
        print(f"Total unique terms in file: {len(search_terms)}")
        print(f"Successfully processed (attempted extraction): {processed_count}")
        print(f"Skipped items: {len(skipped_items)}")
        if skipped_items:
            print("\nSkipped Items Details:")
            for skipped in skipped_items:
                print(f"- {skipped}")
                
            with open("skipped_items.txt", "w") as f:
                for skipped in skipped_items:
                    f.write(skipped + "\n")
            print("\nSkipped items also saved to 'skipped_items.txt'")

# --- How to run the script ---
if __name__ == "__main__":
    test_file_name = 'sample_data.xlsx'
    
    # Create a dummy file for demonstration
    pd.DataFrame({
        'District Name': ['Los Angeles Unified', 'San Francisco Unified', 'Manteca Unified', 'Non-existent District'],
        'Other Data': ['Info1', 'Info2', 'Info3', 'Info4']
    }).to_excel(test_file_name, index=False)
    print(f"Created a sample '{test_file_name}' for testing.")
    
    # Run the generic scraper using the predefined configuration
    run_scraper_with_config(WEBSITE_CONFIG, test_file_name)

    # # Clean up the dummy file
    # if os.path.exists(test_file_name):
    #     os.remove(test_file_name)
    #     print(f"\nCleaned up '{test_file_name}'.")