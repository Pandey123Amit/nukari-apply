from datetime import date

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.tracker import is_already_applied, save_applied
from src.utils import log_error, log_info, log_warn, random_delay, random_scroll


def handle_apply_flow(driver):
    """Handle different apply types after clicking the apply button.

    Handles Naukri's easy-apply modal, chatbot questions, and external redirects.
    Returns True if application was submitted successfully.
    """
    try:
        wait = WebDriverWait(driver, 10)

        # Check for chatbot/questionnaire modal
        try:
            chatbot = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".chatbot-container, [class*='chatbot'], .apply-dialog"))
            )
            # Try to submit chatbot with default answers
            submit_btns = chatbot.find_elements(By.CSS_SELECTOR, "button[type='submit'], button.submit, button[class*='submit']")
            if submit_btns:
                submit_btns[0].click()
                random_delay(2, 3)
                log_info("  Submitted chatbot/questionnaire")
                return True
        except Exception:
            pass

        # Check for "Already Applied" message
        try:
            already = driver.find_element(By.XPATH, "//*[contains(text(), 'already applied') or contains(text(), 'Already Applied')]")
            if already.is_displayed():
                log_warn("  Already applied to this job")
                return False
        except Exception:
            pass

        # Check for success confirmation
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'applied successfully') or contains(text(), 'Application Submitted') or contains(text(), 'Successfully Applied')]"))
            )
            return True
        except Exception:
            pass

        # If we reach here, assume the apply click itself was enough (easy apply)
        return True

    except Exception as e:
        log_error(f"  Error in apply flow: {e}")
        return False


def _apply_single_job(driver, job):
    """Attempt to apply to a single job. Returns True on success."""
    link = job.get("link", "")
    if not link:
        return False

    try:
        driver.get(link)
        random_delay(3, 5)
        random_scroll(driver)

        wait = WebDriverWait(driver, 10)

        # Find the apply button
        apply_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "button#apply-button, button[class*='apply'], .apply-btn, "
                "button[id*='apply'], .apply-button-container button, "
                "a[class*='apply-button']"
            ))
        )

        # Check if button says "Applied" already
        btn_text = apply_btn.text.strip().lower()
        if "applied" in btn_text:
            log_warn(f"  Already applied: {job.get('title', 'Unknown')}")
            return False

        random_scroll(driver)
        random_delay(1, 2)
        apply_btn.click()
        random_delay(3, 5)

        return handle_apply_flow(driver)

    except Exception as e:
        log_error(f"  Could not apply: {e}")
        return False


def apply_to_jobs(driver, jobs, config):
    """Main apply loop — iterate through jobs and apply.

    Respects daily limits, blacklists, and deduplication via tracker.
    """
    filters = config.get("filters", {})
    max_daily = filters.get("max_daily_apply", 50)
    skip_applied = filters.get("skip_already_applied", True)
    blacklist = [c.lower() for c in filters.get("blacklist_companies", [])]

    applied_count = 0
    skipped_count = 0
    failed_count = 0

    for job in jobs:
        if applied_count >= max_daily:
            log_warn(f"Reached daily apply limit ({max_daily})")
            break

        job_id = job.get("job_id") or job.get("link", "")
        title = job.get("title", "Unknown")
        company = job.get("company", "Unknown")

        # Skip if already applied
        if skip_applied and is_already_applied(job_id):
            log_info(f"  Skipping (already applied): {title} @ {company}")
            skipped_count += 1
            continue

        # Skip blacklisted companies
        if company.lower() in blacklist:
            log_warn(f"  Skipping (blacklisted): {title} @ {company}")
            skipped_count += 1
            continue

        log_info(f"Applying: {title} @ {company}")

        success = _apply_single_job(driver, job)

        if success:
            applied_count += 1
            save_applied({
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": job.get("location", ""),
                "link": job.get("link", ""),
                "date": str(date.today()),
                "status": "applied",
            })
            log_info(f"  Applied successfully ({applied_count}/{max_daily})")
        else:
            failed_count += 1
            log_warn(f"  Failed to apply")

        random_delay(3, 6)

    log_info(f"\nApply session complete: {applied_count} applied, {skipped_count} skipped, {failed_count} failed")
    return {
        "applied": applied_count,
        "skipped": skipped_count,
        "failed": failed_count,
    }
