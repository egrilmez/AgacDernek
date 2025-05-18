import logging
import time
import random
import json
from typing import Dict, List, Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self, username: str, password: str, delay_range: tuple = (2, 5), headless: bool = False):
        self.username = username
        self.password = password
        self.delay_range = delay_range
        self.driver = None
        self.is_logged_in = False
        self.headless = headless
        
    def random_delay(self, min_delay=None, max_delay=None):
        """Add random delay to avoid detection."""
        if min_delay is None:
            min_delay = self.delay_range[0]
        if max_delay is None:
            max_delay = self.delay_range[1]
        time.sleep(random.uniform(min_delay, max_delay))
    
    def setup_driver(self):
        """Initialize Chrome driver with undetected-chromedriver."""
        if not self.driver:
            try:
                options = uc.ChromeOptions()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-notifications')
                options.add_argument('--start-maximized')
                if self.headless:
                    options.add_argument('--headless=new')
                
                # Add random user agent
                ua = UserAgent()
                options.add_argument(f'--user-agent={ua.random}')
                
                self.driver = uc.Chrome(options=options)
                self.driver.set_page_load_timeout(30)
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": ua.random
                })
                
                # Execute stealth JavaScript
                self.driver.execute_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                logger.info("Chrome driver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Chrome driver: {str(e)}")
                raise
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10, condition: str = "presence") -> Optional[object]:
        """Wait for an element with different conditions."""
        try:
            if condition == "presence":
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            elif condition == "clickable":
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
            elif condition == "visible":
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((by, value))
                )
            return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {value}")
            return None
    
    def check_for_challenge(self) -> bool:
        """Check if there's a security challenge and wait for manual intervention."""
        challenge_selectors = [
            "//div[contains(@class, 'challenge')]",
            "//div[contains(@class, 'captcha')]",
            "//div[contains(@class, 'verification')]",
            "//input[@id='verification-code']",
            "//div[contains(text(), 'Security Verification')]",
            "//div[contains(text(), 'Let')]",
            "//div[contains(text(), 'Verify')]"
        ]
        
        for selector in challenge_selectors:
            try:
                if self.driver.find_element(By.XPATH, selector).is_displayed():
                    logger.warning("Security challenge detected! Please solve it manually.")
                    # Save screenshot of the challenge
                    self.driver.save_screenshot("security_challenge.png")
                    # Wait for manual intervention (up to 5 minutes)
                    for _ in range(30):  # 30 * 10 seconds = 5 minutes
                        time.sleep(10)
                        try:
                            # Check if we're logged in
                            if self.driver.find_element(By.CLASS_NAME, "global-nav").is_displayed():
                                logger.info("Successfully logged in after challenge")
                                return True
                        except NoSuchElementException:
                            continue
                    return False
            except NoSuchElementException:
                continue
        return True

    def login(self) -> bool:
        """Login to LinkedIn with enhanced security check handling."""
        if self.is_logged_in:
            return True
            
        try:
            self.setup_driver()
            logger.info("Starting LinkedIn login process...")
            
            # First try going to LinkedIn homepage
            self.driver.get('https://www.linkedin.com')
            self.random_delay(3, 6)
            
            # Save screenshot of initial page
            self.driver.save_screenshot("initial_page.png")
            
            # Check if we're already logged in
            try:
                if self.driver.find_element(By.CLASS_NAME, "global-nav").is_displayed():
                    logger.info("Already logged in to LinkedIn")
                    self.is_logged_in = True
                    return True
            except:
                logger.info("Not already logged in, proceeding with login")
            
            # Try to find the sign in button on homepage
            try:
                sign_in_button = self.wait_for_element(
                    By.CSS_SELECTOR, 
                    "a[data-tracking-control-name='guest_homepage-basic_nav-header-signin']",
                    condition="clickable"
                )
                if sign_in_button:
                    sign_in_button.click()
                    logger.info("Clicked sign in button on homepage")
                    self.random_delay(2, 4)
            except:
                # If not found, go directly to login page
                logger.info("No sign in button found, going directly to login page")
                self.driver.get('https://www.linkedin.com/login')
                self.random_delay(2, 4)
            
            # Save screenshot of login page
            self.driver.save_screenshot("login_page.png")
            
            # Wait for username field with multiple attempts
            username_input = None
            username_selectors = [
                (By.ID, "username"),
                (By.NAME, "session_key"),
                (By.CSS_SELECTOR, "input[autocomplete='username']"),
                (By.CSS_SELECTOR, "input[name='session_key']")
            ]
            
            for by, value in username_selectors:
                try:
                    username_input = self.wait_for_element(by, value, timeout=5, condition="visible")
                    if username_input and username_input.is_displayed():
                        break
                except:
                    continue
            
            if not username_input:
                logger.error("Username field not found - saving screenshot")
                self.driver.save_screenshot("username_field_not_found.png")
                return False
            
            # Enter username with human-like typing
            logger.info("Entering username...")
            username_input.clear()
            for char in self.username:
                username_input.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            self.random_delay(1, 2)
            
            # Similar approach for password field
            password_input = None
            password_selectors = [
                (By.ID, "password"),
                (By.NAME, "session_password"),
                (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
                (By.CSS_SELECTOR, "input[name='session_password']")
            ]
            
            for by, value in password_selectors:
                try:
                    password_input = self.wait_for_element(by, value, timeout=5, condition="visible")
                    if password_input and password_input.is_displayed():
                        break
                except:
                    continue
            
            if not password_input:
                logger.error("Password field not found - saving screenshot")
                self.driver.save_screenshot("password_field_not_found.png")
                return False
            
            # Enter password with human-like typing
            logger.info("Entering password...")
            password_input.clear()
            for char in self.password:
                password_input.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            self.random_delay(1, 2)
            
            # Try multiple ways to submit the form
            submit_attempts = [
                lambda: self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click(),
                lambda: self.driver.find_element(By.CSS_SELECTOR, ".sign-in-form__submit-button").click(),
                lambda: password_input.submit(),
                lambda: password_input.send_keys(Keys.RETURN)
            ]
            
            for attempt in submit_attempts:
                try:
                    attempt()
                    logger.info("Successfully submitted login form")
                    break
                except:
                    continue
            
            # Save screenshot after login attempt
            self.driver.save_screenshot("after_login_attempt.png")
            
            # Check for security challenges
            logger.info("Checking for security challenges...")
            if not self.check_for_challenge():
                logger.error("Could not pass security challenge")
                return False
            
            # Wait for successful login with multiple checks
            logger.info("Waiting for successful login...")
            success_elements = [
                (By.CLASS_NAME, "global-nav"),
                (By.ID, "global-nav"),
                (By.CSS_SELECTOR, "nav.global-nav"),
                (By.XPATH, "//nav[contains(@class, 'global-nav')]"),
                (By.CSS_SELECTOR, ".feed-identity-module")
            ]
            
            for by, value in success_elements:
                try:
                    element = self.wait_for_element(by, value, timeout=10, condition="visible")
                    if element and element.is_displayed():
                        self.is_logged_in = True
                        logger.info("Successfully logged in to LinkedIn")
                        return True
                except:
                    continue
            
            logger.error("Failed to verify successful login - saving final screenshot")
            self.driver.save_screenshot("login_failed.png")
            return False
                
        except Exception as e:
            logger.error(f"Failed to login to LinkedIn: {str(e)}")
            if self.driver:
                self.driver.save_screenshot("login_error.png")
            return False
    
    def clean_company_name(self, company_name: str) -> str:
        """Clean company name for better search results."""
        # Remove common legal entity types
        removals = [
            'A.Ş.',
            'Ltd. Şti.',
            'Ltd.Şti.',
            'San. ve Tic.',
            'San.Tic.',
            'Tic. Ltd. Şti.',
            'San. Tic. Ltd. Şti.',
            'San. ve Tic. Ltd. Şti.',
            'San. ve Tic. A.Ş.',
            'Tic. ve San. A.Ş.',
            'İth. İhr.',
            'İml.',
            'Paz.',
            'Dan. Hizm.',
            'Oto.',
            'İnş.',
            'Taahhüt',
            'Elek.',
            'Mad.',
            'Tur.',
            'Sis.',
            'Mak.',
            'Makina',
            'Makine'
        ]
        
        name = company_name
        for removal in removals:
            name = name.replace(removal, '')
        
        # Remove multiple spaces and trim
        name = ' '.join(name.split())
        
        # Remove any remaining punctuation at the end
        name = name.strip(' .,')
        
        logger.info(f"Cleaned company name from '{company_name}' to '{name}'")
        return name

    def search_company(self, company_name: str) -> Optional[str]:
        """Search for a company and return its LinkedIn URL."""
        try:
            # Clean the company name
            cleaned_name = self.clean_company_name(company_name)
            if not cleaned_name:
                logger.warning(f"Company name '{company_name}' was cleaned to empty string")
                return None
            
            # Try different search approaches
            search_attempts = [
                cleaned_name,  # Try the cleaned name first
                cleaned_name.split()[0],  # Try just the first word
                ' '.join(cleaned_name.split()[:2])  # Try first two words
            ]
            
            for search_term in search_attempts:
                logger.info(f"Trying search term: {search_term}")
                
                # Encode search term for URL
                encoded_term = search_term.replace(' ', '%20')
                search_url = f"https://www.linkedin.com/search/results/companies/?keywords={encoded_term}"
                
                self.driver.get(search_url)
                self.random_delay()
                
                # Save screenshot of search results
                self.driver.save_screenshot(f"search_results_{search_term.replace(' ', '_')}.png")
                
                # Try different selectors for company results
                company_selectors = [
                    "a.app-aware-link",  # Standard company link
                    ".search-results__list .entity-result__title-text a",  # Search result title
                    ".search-results .entity-result__title-text a",  # Alternative search result
                    ".reusable-search__result-container a"  # Generic search result container
                ]
                
                for selector in company_selectors:
                    try:
                        company_links = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                        )
                        
                        # Check each link
                        for link in company_links:
                            href = link.get_attribute('href')
                            if href and '/company/' in href:
                                try:
                                    company_text = link.text.strip()
                                    logger.info(f"Found potential match: {company_text} at {href}")
                                    return href
                                except:
                                    continue
                    except:
                        continue
                
                self.random_delay()
            
            logger.warning(f"No company found for any search attempt: {search_attempts}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for company {company_name}: {str(e)}")
            if self.driver:
                self.driver.save_screenshot("company_search_error.png")
            return None
    
    def get_company_employees(self, company_url: str, max_employees: int = 50) -> List[Dict]:
        """Get employee information from company page."""
        employees = []
        try:
            # Go to company's employees page
            employees_url = f"{company_url}/people/"
            logger.info(f"Navigating to employees page: {employees_url}")
            self.driver.get(employees_url)
            self.random_delay()
            
            # Save screenshot of initial employees page
            self.driver.save_screenshot("employees_page.png")
            
            # Try to find the total number of employees
            try:
                total_text = self.driver.find_element(By.CSS_SELECTOR, ".org-people__header-spacing h2").text
                logger.info(f"Found employee count text: {total_text}")
            except:
                logger.warning("Could not find total employee count")
            
            # Scroll to load more employees
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            employee_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 10
            
            while employee_count < max_employees and scroll_attempts < max_scroll_attempts:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay()
                scroll_attempts += 1
                
                # Try different selectors for employee cards
                employee_selectors = [
                    "org-people-profile-card",
                    "org-people-profile-card__profile-info",
                    "artdeco-entity-lockup__content",
                    "org-grid__content-height-enforcer"
                ]
                
                found_employees = []
                for selector in employee_selectors:
                    try:
                        found_employees = self.driver.find_elements(By.CLASS_NAME, selector)
                        if found_employees:
                            logger.info(f"Found {len(found_employees)} employees with selector: {selector}")
                            break
                    except:
                        continue
                
                if not found_employees:
                    logger.warning("No employee elements found with any selector")
                    # Save screenshot when no employees found
                    self.driver.save_screenshot(f"no_employees_found_{scroll_attempts}.png")
                    continue
                
                # Process new employees
                for card in found_employees[employee_count:]:
                    try:
                        # Try different selectors for employee details
                        name = ""
                        title = ""
                        location = ""
                        
                        # Name selectors
                        name_selectors = [
                            ".org-people-profile-card__profile-title",
                            ".artdeco-entity-lockup__title",
                            ".org-people-profile-card__profile-info a",
                            ".ember-view .org-person-card-content__name"
                        ]
                        
                        for selector in name_selectors:
                            try:
                                name_elem = card.find_element(By.CSS_SELECTOR, selector)
                                name = name_elem.text.strip()
                                if name:
                                    break
                            except:
                                continue
                        
                        # Title selectors
                        title_selectors = [
                            ".org-people-profile-card__profile-info",
                            ".artdeco-entity-lockup__subtitle",
                            ".org-people-profile-card__profile-item",
                            ".ember-view .org-person-card-content__title"
                        ]
                        
                        for selector in title_selectors:
                            try:
                                title_elem = card.find_element(By.CSS_SELECTOR, selector)
                                title = title_elem.text.strip()
                                if title:
                                    break
                            except:
                                continue
                        
                        # Location selectors
                        location_selectors = [
                            ".org-people-profile-card__location",
                            ".artdeco-entity-lockup__caption",
                            ".org-people-profile-card__location-text",
                            ".ember-view .org-person-card-content__location"
                        ]
                        
                        for selector in location_selectors:
                            try:
                                location_elem = card.find_element(By.CSS_SELECTOR, selector)
                                location = location_elem.text.strip()
                                if location:
                                    break
                            except:
                                continue
                        
                        if name or title:  # At least one of these should be present
                            employee_data = {
                                'name': name,
                                'title': title,
                                'location': location
                            }
                            
                            if employee_data not in employees:  # Avoid duplicates
                                employees.append(employee_data)
                                employee_count += 1
                                logger.info(f"Added employee: {name} ({title})")
                                
                                if employee_count >= max_employees:
                                    break
                            
                    except Exception as e:
                        logger.warning(f"Error extracting employee info: {str(e)}")
                        continue
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1  # Increment attempts if no new content loaded
                else:
                    scroll_attempts = 0  # Reset attempts if new content was loaded
                    last_height = new_height
                
                # Save screenshot periodically
                if scroll_attempts % 3 == 0:
                    self.driver.save_screenshot(f"employees_scroll_{scroll_attempts}.png")
            
            if not employees:
                logger.warning("No employees found - saving final screenshot")
                self.driver.save_screenshot("no_employees_final.png")
            else:
                logger.info(f"Found {len(employees)} employees")
            
            return employees
            
        except Exception as e:
            logger.error(f"Error getting employees from {company_url}: {str(e)}")
            if self.driver:
                self.driver.save_screenshot("employee_scraping_error.png")
            return []
    
    def scrape_company_employees(self, company_name: str, max_employees: int = 50) -> List[Dict]:
        """Search for a company and scrape its employees."""
        try:
            if not self.is_logged_in and not self.login():
                logger.error("Not logged in to LinkedIn")
                return []
            
            company_url = self.search_company(company_name)
            if not company_url:
                logger.warning(f"Could not find LinkedIn page for company: {company_name}")
                return []
            
            self.random_delay()
            return self.get_company_employees(company_url, max_employees)
            
        except Exception as e:
            logger.error(f"Error scraping employees for {company_name}: {str(e)}")
            return []
    
    def __del__(self):
        """Cleanup method to ensure the driver is closed."""
        if self.driver:
            self.driver.quit() 