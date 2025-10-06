"""
Web Scraping Service
Handles automated attendance marking using Selenium with final screenshot capture only
"""

import time
from datetime import datetime
from pathlib import Path
import shutil
import platform
from typing import Optional, Dict, Any, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from ..config import settings
from ..logging_config import logger, log_function_call


class ScrapingService:
    """Service for web scraping and attendance automation"""
    
    def __init__(self):
        """Initialize scraping service"""
        self.screenshot_dir = settings.SCREENSHOT_DIR
        logger.info("Scraping Service initialized")
    
    def _setup_driver(self, headless: bool = True) -> webdriver.Chrome:
        """
        Setup Chrome WebDriver with appropriate options
        Optimized for M3 Mac (Apple Silicon)
        
        Args:
            headless: Run browser in headless mode
            
        Returns:
            Configured WebDriver instance
        """
        
        chrome_options = Options()
        
        if headless:
           chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Allow images for screenshots
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
        }
        chrome_options.add_experimental_option('prefs', prefs)
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = None
            driver_path = None
            
            system_driver = shutil.which('chromedriver')
            if system_driver:
                logger.info(f"Found system chromedriver: {system_driver}")
                driver_path = system_driver
            
            if not driver_path:
                homebrew_paths = [
                    '/opt/homebrew/bin/chromedriver',
                    '/usr/local/bin/chromedriver',
                ]
                for path in homebrew_paths:
                    if Path(path).exists():
                        logger.info(f"Found chromedriver at: {path}")
                        driver_path = path
                        break
            
            if not driver_path:
                logger.info("Using ChromeDriverManager to download driver...")
                try:
                    downloaded_path = ChromeDriverManager().install()
                    
                    if 'THIRD_PARTY_NOTICES' in downloaded_path or not downloaded_path.endswith('chromedriver'):
                        driver_dir = Path(downloaded_path).parent
                        possible_drivers = list(driver_dir.glob('**/chromedriver'))
                        possible_drivers = [p for p in possible_drivers if not any(
                            x in p.name for x in ['THIRD_PARTY', '.txt', '.html']
                        )]
                        
                        if possible_drivers:
                            driver_path = str(possible_drivers[0])
                            logger.info(f"Found correct chromedriver: {driver_path}")
                        else:
                            raise Exception("Could not find valid chromedriver executable")
                    else:
                        driver_path = downloaded_path
                        
                except Exception as e:
                    logger.error(f"ChromeDriverManager failed: {str(e)}")
                    raise
            
            if not Path(driver_path).exists():
                raise Exception(f"ChromeDriver not found at: {driver_path}")
            
            Path(driver_path).chmod(0o755)
            service = Service(driver_path)
            
            logger.info(f"Initializing Chrome WebDriver with: {driver_path}")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info(f"Chrome WebDriver initialized successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}", exc_info=True)
            
            arch = platform.machine()
            error_msg = f"WebDriver initialization failed on {arch} architecture"
            
            if arch == 'arm64':
                error_msg += "\n\nTry installing chromedriver via homebrew:\n"
                error_msg += "  brew install --cask chromedriver\n"
                error_msg += "  xattr -d com.apple.quarantine $(which chromedriver)"
            
            raise Exception(f"{error_msg}\n\nOriginal error: {str(e)}")
    
    @log_function_call
    def mark_attendance(
        self,
        qr_url: str,
        username: str,
        password: str,
        capture_all_steps: bool = False
    ) -> Dict[str, Any]:
        """
        Automate attendance marking process with final screenshot capture only
        
        Args:
            qr_url: QR code URL to access
            username: NSBM login username (REQUIRED)
            password: NSBM login password (REQUIRED)
            capture_all_steps: Capture screenshots at each step (default: False)
            
        Returns:
            Dictionary containing success status, final screenshot, and path
            
        Raises:
            Exception: If attendance marking fails
        """
        
        driver = None
        final_screenshot_path = None
        
        try:
            # Validate credentials are provided
            if not username or not password:
                raise ValueError("Username and password are required for attendance marking")
            
            logger.info(f"Starting attendance marking process for URL: {qr_url}")
            logger.info(f"Using username: {username}")
            
            driver = self._setup_driver(headless=True)
            driver.set_page_load_timeout(30)
            
            # Step 1: Navigate to QR URL
            logger.info("Step 1: Navigating to QR URL...")
            driver.get(qr_url)
            time.sleep(2)
            
            # Step 2: Login
            logger.info("Step 2: Logging in...")
            self._perform_login(driver, username, password)
            time.sleep(3)
            
            # Step 3: Handle details page and click OK
            logger.info("Step 3: Confirming attendance...")
            self._confirm_attendance(driver)
            time.sleep(3)
            
            # Step 4: Wait for thank you page and capture ONLY final screenshot
            logger.info("Step 4: Waiting for confirmation page...")
            final_screenshot_path = self._capture_confirmation(driver)
            
            logger.info(f"Attendance marked successfully! Screenshot: {final_screenshot_path}")
            
            return {
                "success": True,
                "message": "Attendance marked successfully",
                "screenshot_path": final_screenshot_path,
                "screenshot_filename": Path(final_screenshot_path).name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except TimeoutException as e:
            logger.error(f"Timeout during attendance marking: {str(e)}")
            
            # Capture error screenshot and return it
            error_screenshot_path = None
            if driver:
                error_screenshot_path = self._capture_screenshot(driver, "error_timeout")
                logger.warning(f"Error screenshot saved: {error_screenshot_path}")
            
            return {
                "success": False,
                "message": "Page load timeout - please check your internet connection",
                "screenshot_path": error_screenshot_path,
                "screenshot_filename": Path(error_screenshot_path).name if error_screenshot_path else None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        except NoSuchElementException as e:
            logger.error(f"Element not found: {str(e)}")
            
            # Capture error screenshot and return it
            error_screenshot_path = None
            if driver:
                error_screenshot_path = self._capture_screenshot(driver, "error_element_not_found")
                logger.warning(f"Error screenshot saved: {error_screenshot_path}")
            
            return {
                "success": False,
                "message": "Required element not found on page - website structure may have changed",
                "screenshot_path": error_screenshot_path,
                "screenshot_filename": Path(error_screenshot_path).name if error_screenshot_path else None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        except Exception as e:
            logger.error(f"Attendance marking failed: {str(e)}", exc_info=True)
            
            # Capture error screenshot and return it
            error_screenshot_path = None
            if driver:
                try:
                    error_screenshot_path = self._capture_screenshot(driver, "error_general")
                    logger.warning(f"Error screenshot saved: {error_screenshot_path}")
                except:
                    pass
            
            return {
                "success": False,
                "message": f"Attendance marking failed: {str(e)}",
                "screenshot_path": error_screenshot_path,
                "screenshot_filename": Path(error_screenshot_path).name if error_screenshot_path else None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        finally:
            if driver:
                driver.quit()
                logger.info("WebDriver closed")
    
    def _perform_login(self, driver: webdriver.Chrome, username: str, password: str):
        """
        Perform login on NSBM portal
        
        Args:
            driver: WebDriver instance
            username: Login username
            password: Login password
        """
        
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(username)
            logger.debug("Username entered")
            
            password_field = driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(password)
            logger.debug("Password entered")
            
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'].btn.btn-primary")
            login_button.click()
            logger.info("Login button clicked")
            
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise Exception(f"Login process failed: {str(e)}")
    
    def _confirm_attendance(self, driver: webdriver.Chrome):
        """
        Click OK button to confirm attendance
        
        Args:
            driver: WebDriver instance
        """
        
        try:
            ok_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary[onclick='load_win();']"))
            )
            ok_button.click()
            logger.info("OK button clicked - attendance confirmed")
            
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Failed to confirm attendance: {str(e)}")
            raise Exception(f"Attendance confirmation failed: {str(e)}")
    
    def _capture_confirmation(self, driver: webdriver.Chrome) -> str:
        """
        Capture screenshot of final confirmation/thank you page ONLY
        
        Args:
            driver: WebDriver instance
            
        Returns:
            Path to screenshot file
        """
        
        try:
            # Wait for the final "Thank you" page
            thank_you_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Thank you')]"))
            )
            logger.info("Thank you page detected")
            
            # Small delay to ensure page is fully rendered
            time.sleep(1)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"confirmation_{timestamp}.png"
            screenshot_path = self.screenshot_dir / screenshot_filename
            
            # Capture the screenshot
            driver.save_screenshot(str(screenshot_path))
            logger.info(f"Final confirmation screenshot captured: {screenshot_path}")
            
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Failed to capture confirmation: {str(e)}")
            raise Exception(f"Confirmation capture failed: {str(e)}")
    
    def _capture_screenshot(self, driver: webdriver.Chrome, step_name: str) -> str:
        """
        Capture screenshot at any step (used for debugging/errors)
        
        Args:
            driver: WebDriver instance
            step_name: Name/identifier for this screenshot
            
        Returns:
            Path to screenshot file
        """
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"{step_name}_{timestamp}.png"
            screenshot_path = self.screenshot_dir / screenshot_filename
            
            driver.save_screenshot(str(screenshot_path))
            logger.info(f"Screenshot captured: {screenshot_path}")
            
            return str(screenshot_path)
            
        except Exception as e:
            logger.warning(f"Failed to capture screenshot for {step_name}: {str(e)}")
            return None
    
    @log_function_call
    def test_connection(self, url: str) -> bool:
        """
        Test if URL is accessible
        
        Args:
            url: URL to test
            
        Returns:
            True if accessible, False otherwise
        """
        
        driver = None
        try:
            driver = self._setup_driver(headless=True)
            driver.get(url)
            logger.info(f"Successfully accessed URL: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to access URL: {str(e)}")
            return False
        finally:
            if driver:
                driver.quit()


# Singleton instance
scraping_service = ScrapingService()

__all__ = ["scraping_service", "ScrapingService"]