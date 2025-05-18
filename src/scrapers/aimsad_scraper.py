import logging
from typing import Dict, List, Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AimsadScraper:
    def __init__(self, base_url: str = "https://www.aimsad.org/firmalar", delay: int = 2):
        self.base_url = base_url
        self.delay = delay
    
    def get_driver(self):
        """Initialize and return a new Chrome driver."""
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        return driver
            
    def extract_company_details(self, driver, company_element) -> Dict:
        """Extract details from a company element."""
        try:
            # Extract company name
            name = company_element.find_element(By.CLASS_NAME, "old-president__title").text.strip()
            
            # Extract company details
            details = company_element.find_element(By.CLASS_NAME, "sub-search__address--txt").text
            address = details.replace("Adres :", "").strip() if "Adres :" in details else ""
            # Clean up address - replace newlines with spaces
            address = " ".join(address.split())
            
            # Extract contact information
            contact_elements = company_element.find_elements(By.CLASS_NAME, "map-search-inf__item")
            phone = ""
            fax = ""
            email = ""
            
            for contact in contact_elements:
                contact_text = contact.text
                if "Telefon" in contact_text:
                    phone = contact_text.replace("Telefon :", "").strip()
                elif "Faks" in contact_text:
                    fax = contact_text.replace("Faks :", "").strip()
                elif "E-Posta" in contact_text:
                    email = contact_text.replace("E-Posta :", "").strip()
            
            company_data = {
                'name': name,
                'address': address,
                'phone': phone,
                'fax': fax,
                'email': email
            }
            
            logger.info(f"Extracted company data: {company_data}")
            return company_data
            
        except Exception as e:
            logger.error(f"Error extracting company details: {str(e)}")
            return None
    
    def scrape_page(self, page_number: int) -> List[Dict]:
        """Scrape a single page of company information."""
        companies = []
        driver = None
        
        try:
            driver = self.get_driver()
            url = f"{self.base_url}/yurtici/{page_number}" if page_number > 1 else self.base_url
            logger.info(f"Scraping page {page_number}: {url}")
            
            driver.get(url)
            time.sleep(5)  # Increased wait time for page load
            
            # Wait for the company elements to be present
            company_elements = WebDriverWait(driver, 30).until(  # Increased timeout
                EC.presence_of_all_elements_located((By.CLASS_NAME, "old-president__element"))
            )
            
            # Additional wait to ensure all elements are fully loaded
            time.sleep(2)
            
            logger.info(f"Found {len(company_elements)} company elements on page {page_number}")
            
            for element in company_elements:
                company_data = self.extract_company_details(driver, element)
                if company_data:
                    companies.append(company_data)
                    time.sleep(0.5)  # Small delay between processing each company
            
        except Exception as e:
            logger.error(f"Error scraping page {page_number}: {str(e)}")
        finally:
            if driver:
                driver.quit()
                
        return companies
    
    def scrape_companies(self) -> List[Dict]:
        """Scrape company information from all pages."""
        all_companies = []
        
        # Scrape each page
        for page in range(1, 7):  # 6 pages total
            companies = self.scrape_page(page)
            all_companies.extend(companies)
            time.sleep(self.delay)  # Wait between pages
            
        logger.info(f"Successfully scraped {len(all_companies)} companies")
        return all_companies

    def __del__(self):
        """Cleanup method to ensure the driver is closed."""
        if self.driver:
            self.driver.quit() 