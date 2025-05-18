import os
import logging
import pandas as pd
from dotenv import load_dotenv
from scrapers.aimsad_scraper import AimsadScraper
from scrapers.linkedin_scraper import LinkedInScraper
from typing import Dict, List
import time
import random
import json
import csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Load environment variables and create necessary directories."""
    load_dotenv()
    
    # Create output directory if it doesn't exist
    output_dir = os.getenv('OUTPUT_DIR', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    return {
        'linkedin_username': os.getenv('LINKEDIN_USERNAME'),
        'linkedin_password': os.getenv('LINKEDIN_PASSWORD'),
        'output_dir': output_dir,
        'companies_file': os.getenv('COMPANIES_FILE', 'output/companies.csv'),
        'employees_file': os.getenv('EMPLOYEES_FILE', 'output/employees.csv'),
        'max_employees_per_company': int(os.getenv('MAX_EMPLOYEES_PER_COMPANY', '50'))
    }

def scrape_aimsad_companies() -> List[Dict]:
    """Scrape company information from AIMSAD website."""
    try:
        # Initialize scraper
        scraper = AimsadScraper()
        
        # Get companies
        logger.info("Starting AIMSAD scraping...")
        companies = scraper.scrape_companies()
        logger.info(f"Found {len(companies)} companies")
        
        # Save results
        if companies:
            # Save to JSON for inspection
            with open("output/companies.json", "w", encoding="utf-8") as f:
                json.dump(companies, f, ensure_ascii=False, indent=2)
            
            # Save to CSV
            df = pd.DataFrame(companies)
            df = df[['name', 'address', 'phone', 'fax', 'email']]  # Ensure column order
            df.to_csv(
                "output/companies.csv",
                index=False,
                encoding='utf-8-sig',  # For proper Turkish character encoding
                quoting=csv.QUOTE_ALL  # Quote all fields to handle special characters
            )
            logger.info("Results saved to output/companies.csv and output/companies.json")
        else:
            logger.error("No companies were found!")
            
        return companies
            
    except Exception as e:
        logger.error(f"Error scraping AIMSAD companies: {str(e)}", exc_info=True)
        return []

def scrape_linkedin_employees(companies: List[Dict], config: Dict) -> List[Dict]:
    """Scrape employee information from LinkedIn for each company."""
    all_employees = []
    
    try:
        # Initialize LinkedIn scraper
        linkedin_scraper = LinkedInScraper(
            username=config['linkedin_username'],
            password=config['linkedin_password'],
            headless=True
        )
        
        # Process each company
        for company in companies:
            company_name = company['name']
            logger.info(f"Scraping LinkedIn data for company: {company_name}")
            
            employees = linkedin_scraper.scrape_company_employees(
                company_name,
                max_employees=config['max_employees_per_company']
            )
            
            # Add company information to each employee record
            for employee in employees:
                employee.update({
                    'company_name': company['name'],
                    'company_address': company['address'],
                    'company_phone': company['phone'],
                    'company_fax': company['fax'],
                    'company_email': company['email']
                })
                all_employees.append(employee)
            
            # Random delay between companies
            time.sleep(random.uniform(5, 10))
        
        # Save results
        if all_employees:
            # Save to JSON for inspection
            with open("output/employees.json", "w", encoding="utf-8") as f:
                json.dump(all_employees, f, ensure_ascii=False, indent=2)
            
            # Save to CSV
            df = pd.DataFrame(all_employees)
            df.to_csv(
                config['employees_file'],
                index=False,
                encoding='utf-8-sig',  # For proper Turkish character encoding
                quoting=csv.QUOTE_ALL  # Quote all fields to handle special characters
            )
            logger.info(f"Employee data saved to {config['employees_file']}")
        else:
            logger.warning("No employee data was found!")
        
        return all_employees
        
    except Exception as e:
        logger.error(f"Error scraping LinkedIn data: {str(e)}", exc_info=True)
        return []

def main():
    """Main function to run both scrapers."""
    try:
        # Load configuration
        config = setup_environment()
        
        # Check if we have LinkedIn credentials
        if not config['linkedin_username'] or not config['linkedin_password']:
            logger.error("LinkedIn credentials not found in environment variables")
            return
        
        # First, scrape AIMSAD companies if we don't have them already
        if not os.path.exists(config['companies_file']):
            companies = scrape_aimsad_companies()
        else:
            # Load existing companies data
            df = pd.read_csv(config['companies_file'])
            companies = df.to_dict('records')
            logger.info(f"Loaded {len(companies)} companies from {config['companies_file']}")
        
        if not companies:
            logger.error("No companies data available")
            return
        
        # Then scrape LinkedIn data for each company
        employees = scrape_linkedin_employees(companies, config)
        logger.info(f"Scraped {len(employees)} employees from LinkedIn")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 