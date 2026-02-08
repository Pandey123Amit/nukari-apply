import os
import pickle

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.utils import human_type, log_error, log_info, log_warn, random_delay

load_dotenv()

COOKIES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cookies.pkl")
LOGIN_URL = "https://www.naukri.com/nlogin/login"
HOME_URL = "https://www.naukri.com/mnjuser/homepage"


def save_cookies(driver):
    """Save browser cookies to disk."""
    os.makedirs(os.path.dirname(COOKIES_PATH), exist_ok=True)
    with open(COOKIES_PATH, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    log_info(f"Cookies saved to {COOKIES_PATH}")


def load_cookies(driver):
    """Load cookies from disk into the browser session."""
    if not os.path.exists(COOKIES_PATH):
        log_warn("No saved cookies found")
        return False

    driver.get("https://www.naukri.com")
    random_delay(2, 4)

    with open(COOKIES_PATH, "rb") as f:
        cookies = pickle.load(f)

    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass

    driver.refresh()
    random_delay(2, 4)
    log_info("Cookies loaded from disk")
    return True


def is_logged_in(driver):
    """Check if the user is currently logged in."""
    try:
        driver.get(HOME_URL)
        random_delay(3, 5)
        # Check multiple indicators of logged-in state
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                ".nI-gNb-drawer__hamburger, "
                ".view-profile-wrapper, "
                "a[href*='mnjuser/profile'], "
                "[class*='user-name'], "
                ".nI-gNb-header__wrapper, "
                "#root .dashboard-container"
            ))
        )
        # Also verify we weren't redirected back to login
        if "nlogin/login" in driver.current_url:
            log_warn("Redirected to login page — not logged in")
            return False
        log_info("Session is active — already logged in")
        return True
    except Exception:
        log_warn("Session expired or not logged in")
        return False


def login(driver):
    """Login to Naukri using credentials from .env. Tries cookies first."""
    # Try cookie-based session restoration first
    if os.path.exists(COOKIES_PATH):
        log_info("Attempting session restore from cookies...")
        load_cookies(driver)
        if is_logged_in(driver):
            return True

    # Fresh login
    email = os.getenv("NAUKRI_EMAIL", "").strip()
    password = os.getenv("NAUKRI_PASSWORD", "").strip()

    if not email or not password:
        log_error("Missing NAUKRI_EMAIL or NAUKRI_PASSWORD in .env file")
        return False

    log_info(f"Performing fresh login for {email}...")
    driver.get(LOGIN_URL)
    random_delay(3, 5)

    try:
        wait = WebDriverWait(driver, 15)

        # Enter email
        email_field = wait.until(
            EC.presence_of_element_located((By.ID, "usernameField"))
        )
        email_field.clear()
        human_type(email_field, email)
        random_delay(1, 2)

        # Enter password
        password_field = wait.until(
            EC.presence_of_element_located((By.ID, "passwordField"))
        )
        password_field.clear()
        human_type(password_field, password)
        random_delay(1, 2)

        # Click the Login button (not the search submit)
        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(text(),'Login')]"))
        )
        login_btn.click()
        random_delay(5, 8)

        # Take screenshot for debugging
        driver.save_screenshot("/tmp/naukri_after_login.png")

        # Verify login succeeded
        if is_logged_in(driver):
            save_cookies(driver)
            log_info("Login successful!")
            return True
        else:
            log_error("Login failed — could not verify session")
            driver.save_screenshot("/tmp/naukri_login_failed.png")
            return False

    except Exception as e:
        log_error(f"Login failed: {e}")
        driver.save_screenshot("/tmp/naukri_login_error.png")
        return False
