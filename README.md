School Directory Web Scraper

A Python-based web scraping tool designed to automatically extract and structure contact information from public school directories. Leveraging Selenium for browser automation and pandas for data handling, this project demonstrates a reusable approach to collecting structured data from the web.

This project was developed to showcase skills gained during a software development internship, focusing on data manipulation, automation, and creating clean, reusable code.

Key Features

    Automated Data Extraction: Scrapes contact names, job titles, emails, and phone numbers from specific website sections.

    Structured Data Output: Stores all scraped contact information in a clean, organized format within an Excel file, with each data point residing in its own cell for easy analysis.

    Dynamic Web Navigation: Automatically navigates from a search results page to individual district detail pages to extract information.

    Error Handling: Skips districts that cannot be found and logs them to a separate file, ensuring the script completes without interruption.

    Reusable Configuration: The scraper's behavior is controlled by a central configuration dictionary, allowing for easy adaptation to other similar websites.

Technologies Used

    Python: The core programming language for the script.

    Selenium: Used for browser automation to interact with the website dynamically.

    pandas: A powerful library for data manipulation and working with Excel files.

    openpyxl: Enables the script to read from and write to .xlsx files.

Getting Started
Prerequisites

    Python 3.x installed

    Firefox web browser and geckodriver installed and added to your system's PATH.

Installation

    Clone this repository to your local machine:

    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)

    Navigate to the project directory:

    cd your-repo-name

    Install the required Python libraries using the provided requirements.txt file:

    pip install -r requirements.txt

Usage

    Run the script:

    python scraper.py

    The script will automatically create a sample Excel file named sample_data.xlsx for testing purposes. If you want to scrape your own data, simply create an Excel file with a column named District Name and place it in the same directory. Then, update the test_file_name variable in scraper.py to match your file's name.

    The script will launch a browser, process each district, and save the extracted contact information directly back to your Excel file. Any districts that could not be found will be logged to skipped_items.txt.

File Structure

    scraper.py: The main script that performs all scraping and data handling.

    requirements.txt: Lists all Python dependencies required to run the script.

    README.md: This file, providing an overview and instructions.

    sample_data.xlsx: An Excel file created by the script for testing, which will be automatically deleted upon completion.

    skipped_items.txt: A log file that is created at runtime, listing any districts that were skipped during the process.
