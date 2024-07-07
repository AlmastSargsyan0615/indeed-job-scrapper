import json
import csv
import urllib.parse
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

# Load the keyword.json file
with open('keyword.json', 'r') as file:
    data = json.load(file)

# Define the base URL
base_url = "https://www.indeed.com/jobs"

# Set options for headless mode
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # Uncomment this line if you want to run in headless mode
options.add_argument("--window-size=1920,1200")

# Initialize ChromeDriver
driver = webdriver.Chrome(options=options)

i = 0
i_limit = 30
end_flag = False
job_items = []
job_ids = []

# Get current date and time for the filename
now = datetime.now()
date_time_str = now.strftime("%Y%m%d_%H%M%S")

# Open Chrome and scrape each search pair
for pair in data['pairs']:
    # Define the search parameters
    query_parameters = {
        "q": pair['q'],
        "l": pair['l']
    }

    # Construct the CSV filename using q, l, and current date and time
    filename = f"{pair['q'].replace(' ', '_')}_{pair['l'].replace(' ', '_')}_{date_time_str}.csv"
    
    # Open the CSV file in write mode
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Write the header row
        csvwriter.writerow(["Job Link", "Salary Info", "Company Link"])

        # Encode the parameters and construct the full URL
        encoded_parameters = urllib.parse.urlencode(query_parameters)
        while True:
            if i > i_limit:
                print("limited!")
                break
            full_url = f"{base_url}?{encoded_parameters}&start={i * 10}"
            i = i + 1
            print(f"Scraping jobs for: {pair['q']} in {pair['l']}")
            print(f"URL: {full_url}")

            # Visit the URL
            driver.get(full_url)

            try:
                # Wait for the job cards container to be present
                jobcards = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "mosaic-provider-jobcards"))
                )

                # Find the <ul> element inside the job cards container with class "css-zu9cdh eu4oa1w0"
                ul_element = jobcards.find_element(By.CSS_SELECTOR, "ul.css-zu9cdh.eu4oa1w0")

                # Find all <li> elements with class "css-5lfssm eu4oa1w0" inside the <ul> element
                li_elements = ul_element.find_elements(By.CSS_SELECTOR, "li.css-5lfssm.eu4oa1w0")

                # Print or process each li_element
                for li in li_elements:
                    try:
                        # Find the first-level <div> inside the <li> element
                        first_level_div = li.find_element(By.CSS_SELECTOR, 'div:first-child')

                        # Get the class name of the first-level <div>
                        div_class = first_level_div.get_attribute("class")

                        # Regular expression pattern to find "job_" followed by alphanumeric characters
                        pattern = r'\bjob_(\w+)\b'

                        # Find all matches in the text
                        matches = re.findall(pattern, div_class)

                        # If there are matches, extract the first one (or handle multiple matches as needed)
                        if matches:
                            job_id = matches[0]
                            print("===========================", job_id)
                            if job_id not in job_ids:
                                try:
                                    # Find the <a> tag with id="xxx"
                                    page_id = ((li.find_element(By.ID, "job_" + job_id)).get_attribute("data-mobtk")).replace(" ", "-")
                                    print(f'Found <a> tag: {page_id}')
                                    company_name = ((li.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']")).text).replace(" ", "-")
                                    print(f'Found <span> tag: {company_name}')
                                    info_url = f"{base_url}?{encoded_parameters}&vjk={job_id}"
                                    sub_url = f"https://www.indeed.com/cmp/{company_name}?campaignid=mobvjcmp&from=mobviewjob&tk={page_id}&fromjk={job_id}"
                                    print(info_url)
                                    print(sub_url)
                                except Exception as e:
                                    print(f'Error: {e}')
                                job_ids.append(job_id)
                                job_items.append((info_url, sub_url))
                            else:
                                end_flag = True
                                break
                    except Exception as e:
                        print(f"Error finding first-level div: {e}")
                if end_flag:
                    print("repeated!")
                    break
            except Exception as e:
                print(f"Error scraping jobs: {e}")

        # Print the list of extracted job items
        print("Job items:", job_items, len(job_items))
        for job_item in job_items:
            driver.get(job_item[0])
            # Locate the div with id="salaryInfoAndJobType"
            try:
                div_element = driver.find_element(By.ID, "salaryInfoAndJobType")

                # Find the first span within this div
                first_span = div_element.find_element(By.TAG_NAME, "span")
                if '$' not in first_span.text:
                    salary_info = 'N/A'
                else:
                    # Retrieve the text of this span
                    salary_info = first_span.text

            except:
                salary_info = 'N/A'
            print("salary info", salary_info)
            time.sleep(1)
            driver.get(job_item[1])
            try:
                company_name = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[@data-testid='companyLink[]']"))).get_attribute('href')
            except:
                company_name = "N/A"

            print("web link", company_name)
            
            # Write the job link, salary info, and company link to the CSV file
            csvwriter.writerow([job_item[0], salary_info, company_name])
            time.sleep(1)

# Close the WebDriver session
driver.quit()
