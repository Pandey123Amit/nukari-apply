import re
import subprocess

import undetected_chromedriver as uc

from src.utils import log_info, setup_logger

logger = setup_logger()


def _get_chrome_major_version():
    """Detect the installed Chrome major version."""
    try:
        output = subprocess.check_output(
            ["google-chrome", "--version"], stderr=subprocess.DEVNULL, text=True
        )
        match = re.search(r"(\d+)\.", output)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None


def create_driver(headless=True):
    """Create an undetected Chrome driver with anti-detection settings."""
    options = uc.ChromeOptions()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")

    version = _get_chrome_major_version()
    if version:
        log_info(f"Detected Chrome version: {version}")

    driver = uc.Chrome(
        options=options,
        use_subprocess=True,
        version_main=version,
    )
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)

    log_info("Browser launched successfully")
    return driver
