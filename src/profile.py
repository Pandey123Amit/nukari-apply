from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.utils import human_type, log_error, log_info, log_warn, random_delay, random_scroll

PROFILE_URL = "https://www.naukri.com/mnjuser/profile"


def update_skills(driver, skills_list):
    """Navigate to profile and update key skills."""
    if not skills_list:
        log_warn("No skills provided to update")
        return False

    log_info("Updating profile skills...")
    driver.get(PROFILE_URL)
    random_delay(3, 5)
    random_scroll(driver)

    try:
        wait = WebDriverWait(driver, 15)

        # Find and click the key skills edit button
        skills_section = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".keySkills, .key-skill, [class*='keySkill']"))
        )
        random_scroll(driver)
        random_delay(1, 2)

        # Click edit icon near key skills
        edit_btn = skills_section.find_element(By.CSS_SELECTOR, ".edit-icon, span[class*='edit'], .editIcon")
        edit_btn.click()
        random_delay(2, 3)

        # Clear existing skills input and add new ones
        skills_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[class*='skillInput'], input[placeholder*='skill' i], .chipEditor input"))
        )

        for skill in skills_list:
            skills_input.clear()
            human_type(skills_input, skill)
            random_delay(0.5, 1)
            skills_input.send_keys(Keys.ENTER)
            random_delay(0.5, 1)

        # Save
        save_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.save, button[type='submit'], button[class*='save' i]"))
        )
        save_btn.click()
        random_delay(2, 3)

        log_info(f"Skills updated: {', '.join(skills_list)}")
        return True

    except Exception as e:
        log_error(f"Failed to update skills: {e}")
        return False


def update_resume_headline(driver, headline):
    """Update the resume headline on the profile."""
    if not headline:
        log_warn("No headline provided")
        return False

    log_info("Updating resume headline...")
    driver.get(PROFILE_URL)
    random_delay(3, 5)

    try:
        wait = WebDriverWait(driver, 15)

        # Find resume headline section
        headline_section = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".resumeHeadline, [class*='resumeHeadline'], [class*='headline']"))
        )
        random_scroll(driver)
        random_delay(1, 2)

        # Click edit
        edit_btn = headline_section.find_element(By.CSS_SELECTOR, ".edit-icon, span[class*='edit'], .editIcon")
        edit_btn.click()
        random_delay(2, 3)

        # Clear and type new headline
        textarea = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, input[class*='headline' i]"))
        )
        textarea.clear()
        random_delay(0.5, 1)
        human_type(textarea, headline)
        random_delay(1, 2)

        # Save
        save_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.save, button[type='submit'], button[class*='save' i]"))
        )
        save_btn.click()
        random_delay(2, 3)

        log_info(f"Headline updated: {headline}")
        return True

    except Exception as e:
        log_error(f"Failed to update headline: {e}")
        return False


def refresh_profile(driver):
    """Make a minor edit to trigger Naukri's 'profile updated' boost.

    Toggles a trailing space on the resume headline to signal an update
    without changing visible content.
    """
    log_info("Refreshing profile to boost visibility...")
    driver.get(PROFILE_URL)
    random_delay(3, 5)

    try:
        wait = WebDriverWait(driver, 15)

        headline_section = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".resumeHeadline, [class*='resumeHeadline'], [class*='headline']"))
        )
        random_scroll(driver)
        random_delay(1, 2)

        edit_btn = headline_section.find_element(By.CSS_SELECTOR, ".edit-icon, span[class*='edit'], .editIcon")
        edit_btn.click()
        random_delay(2, 3)

        textarea = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, input[class*='headline' i]"))
        )

        current_text = textarea.get_attribute("value") or ""
        # Toggle trailing space
        if current_text.endswith(" "):
            new_text = current_text.rstrip()
        else:
            new_text = current_text + " "

        textarea.clear()
        random_delay(0.5, 1)
        human_type(textarea, new_text)
        random_delay(1, 2)

        save_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.save, button[type='submit'], button[class*='save' i]"))
        )
        save_btn.click()
        random_delay(2, 3)

        log_info("Profile refreshed successfully")
        return True

    except Exception as e:
        log_error(f"Failed to refresh profile: {e}")
        return False
