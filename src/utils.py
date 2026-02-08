import logging
import os
import random
import time
from logging.handlers import RotatingFileHandler

from colorama import Fore, Style, init

init(autoreset=True)

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def setup_logger():
    """Configure file + console logging with rotation."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("nakuri")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    # Rotating file handler — 5 MB max, keep 3 backups
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_fmt)

    # Console handler with color
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def random_delay(min_s=2.0, max_s=5.0):
    """Sleep for a random duration to mimic human behavior."""
    delay = random.uniform(min_s, max_s)
    logging.getLogger("nakuri").debug(f"Sleeping {delay:.1f}s")
    time.sleep(delay)


def human_type(element, text, min_delay=0.05, max_delay=0.15):
    """Type text character by character with random inter-key delays."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))


def random_scroll(driver):
    """Scroll page by a random amount to simulate human browsing."""
    scroll_amount = random.randint(200, 600)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    time.sleep(random.uniform(0.3, 0.8))


def log_info(msg):
    print(f"{Fore.GREEN}[+] {msg}{Style.RESET_ALL}")
    logging.getLogger("nakuri").info(msg)


def log_warn(msg):
    print(f"{Fore.YELLOW}[!] {msg}{Style.RESET_ALL}")
    logging.getLogger("nakuri").warning(msg)


def log_error(msg):
    print(f"{Fore.RED}[-] {msg}{Style.RESET_ALL}")
    logging.getLogger("nakuri").error(msg)
