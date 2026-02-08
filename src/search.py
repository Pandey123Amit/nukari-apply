import urllib.parse

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.utils import log_error, log_info, log_warn, random_delay, random_scroll

SEARCH_BASE_URL = "https://www.naukri.com"


def _build_search_url(keyword, config):
    """Build a Naukri search URL from keyword and config filters."""
    search_cfg = config.get("search", {})
    location = search_cfg.get("location", [])
    experience = search_cfg.get("experience", {})
    salary_min = search_cfg.get("salary_min", 0)

    # Naukri URL pattern: /keyword-jobs-in-location
    keyword_slug = keyword.lower().replace(" ", "-")
    location_slug = "-".join(loc.lower() for loc in location) if location else ""

    url = f"{SEARCH_BASE_URL}/{keyword_slug}-jobs"
    if location_slug:
        url += f"-in-{location_slug}"

    # Query params
    params = {}
    exp_min = experience.get("min")
    exp_max = experience.get("max")
    if exp_min is not None:
        params["experience"] = f"{exp_min}"
    if exp_max is not None:
        params["experience"] = f"{exp_min or 0}-{exp_max}" if exp_min is not None else f"0-{exp_max}"
    if salary_min:
        params["salary"] = str(salary_min)

    if params:
        url += "?" + urllib.parse.urlencode(params)

    return url


def parse_job_listings(driver):
    """Extract job cards from the current search results page."""
    jobs = []

    try:
        wait = WebDriverWait(driver, 10)
        job_cards = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".srp-jobtuple-wrapper, article.jobTuple, .cust-job-tuple, [class*='jobTuple']"))
        )

        for card in job_cards:
            try:
                title_el = card.find_element(By.CSS_SELECTOR, "a.title, a[class*='title'], .job-title a, h2 a")
                title = title_el.text.strip()
                link = title_el.get_attribute("href") or ""

                try:
                    company = card.find_element(By.CSS_SELECTOR, "a.comp-name, .comp-name, [class*='companyName'], .subTitle a").text.strip()
                except Exception:
                    company = "Unknown"

                try:
                    location = card.find_element(By.CSS_SELECTOR, ".loc, .locWdth, [class*='location'], .location").text.strip()
                except Exception:
                    location = "Unknown"

                try:
                    experience = card.find_element(By.CSS_SELECTOR, ".exp, .expwdth, [class*='experience']").text.strip()
                except Exception:
                    experience = ""

                # Extract job ID from URL
                job_id = ""
                if link:
                    parts = link.rstrip("/").split("-")
                    for part in reversed(parts):
                        cleaned = part.split("?")[0]
                        if cleaned.isdigit():
                            job_id = cleaned
                            break

                if title and link:
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "experience": experience,
                        "link": link,
                        "job_id": job_id,
                    })
            except Exception:
                continue

    except Exception as e:
        log_warn(f"Could not parse job listings: {e}")

    return jobs


def paginate(driver):
    """Navigate to the next page of search results. Returns True if successful."""
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.fright, a[class*='next'], .pagination a:last-child")
        if next_btn.is_displayed() and next_btn.is_enabled():
            random_scroll(driver)
            random_delay(1, 2)
            next_btn.click()
            random_delay(3, 5)
            return True
    except Exception:
        pass

    log_info("No more pages to navigate")
    return False


def search_jobs(driver, config, max_pages=3):
    """Search for jobs on Naukri based on config filters.

    Returns a combined list of job dicts across all keywords and pages.
    """
    keywords = config.get("search", {}).get("keywords", [])
    if not keywords:
        log_error("No search keywords configured")
        return []

    all_jobs = []

    for keyword in keywords:
        url = _build_search_url(keyword, config)
        log_info(f"Searching: {keyword}")
        log_info(f"URL: {url}")

        driver.get(url)
        random_delay(3, 5)

        for page in range(1, max_pages + 1):
            log_info(f"  Page {page}...")
            random_scroll(driver)
            random_delay(1, 2)

            jobs = parse_job_listings(driver)
            log_info(f"  Found {len(jobs)} jobs on page {page}")
            all_jobs.extend(jobs)

            if page < max_pages and not paginate(driver):
                break

    # Deduplicate by job_id
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = job.get("job_id") or job.get("link")
        if key and key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    log_info(f"Total unique jobs found: {len(unique_jobs)}")
    return unique_jobs
