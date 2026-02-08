# Naukri.com Auto-Apply Tool

## Project Overview
CLI-based Python automation tool that logs into Naukri.com, searches for jobs based on configured filters, auto-applies to matching jobs, and auto-updates the user's profile/skills to boost recruiter visibility. Uses Selenium with undetected-chromedriver for anti-detection.

## Project Structure
```
nakuri/
├── requirements.txt          # Dependencies
├── .env                      # Naukri credentials (NAUKRI_EMAIL, NAUKRI_PASSWORD) — gitignored
├── .gitignore
├── config.json               # Job search preferences & filters
├── main.py                   # CLI entry point (argparse with subcommands)
├── CLAUDE.md                 # This file
├── src/
│   ├── __init__.py
│   ├── utils.py              # Random delays, human-like behavior, logger
│   ├── browser.py            # Browser setup (undetected-chromedriver, headless)
│   ├── auth.py               # Login, session save/load via cookies
│   ├── profile.py            # Update skills, refresh profile daily
│   ├── search.py             # Search jobs with keyword/location/exp filters
│   ├── apply.py              # Auto-apply engine (click apply, handle flows)
│   └── tracker.py            # Track applied jobs in JSON, export CSV
├── data/
│   ├── applied.json          # Persistent record of applied jobs
│   └── cookies.pkl           # Saved browser cookies (pickle)
└── logs/
    └── app.log               # Rotating log file
```

---

## Setup (First Time)

```bash
# 1. Create virtual environment & install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Add your Naukri credentials in .env
NAUKRI_EMAIL=your_email@example.com
NAUKRI_PASSWORD=your_password

# 3. Edit config.json with your job preferences (keywords, location, skills, etc.)
```

---

## All Commands

### Activate virtual environment (required before every session)
```bash
source .venv/bin/activate
```

### 1. Login — Save session cookies
```bash
python main.py login                # Headless (no browser window)
python main.py --visible login      # Visible browser (for debugging)
```
- Tries saved cookies first, if expired does fresh login
- Saves cookies to `data/cookies.pkl` for future sessions

### 2. Apply — Search and auto-apply to jobs
```bash
python main.py apply                # Headless, 3 pages per keyword
python main.py apply --pages 5      # Search 5 pages per keyword
python main.py --visible apply      # Visible browser
python main.py --visible apply --pages 5
```
- Searches all keywords from `config.json`
- Skips already-applied jobs and blacklisted companies
- Stops at daily limit (default 50)
- Tracks every application in `data/applied.json`

### 3. Update — Update profile skills & headline
```bash
python main.py update               # Headless
python main.py --visible update     # Visible browser
```
- Updates key skills from `config.json` → `profile.skills`
- Updates resume headline from `config.json` → `profile.headline`
- Refreshes profile (toggles trailing space) to boost visibility

### 4. Status — View application statistics
```bash
python main.py status
```
- Shows total applications, today's count, top companies table
- No browser needed — reads from `data/applied.json`

### 5. Export — Export applied jobs to CSV
```bash
python main.py export               # Exports to data/applied_jobs.csv
python main.py export -o ~/jobs.csv # Export to custom path
```
- No browser needed — reads from `data/applied.json`

---

## Config Files

### `.env` — Credentials
```
NAUKRI_EMAIL=your_email@example.com
NAUKRI_PASSWORD=your_password
```

### `config.json` — All Preferences
```json
{
  "search": {
    "keywords": ["Python Developer", "Backend Developer"],
    "location": ["Bangalore", "Remote"],
    "experience": { "min": 0, "max": 2 },
    "salary_min": 600000,
    "job_type": "fulltime"
  },
  "filters": {
    "blacklist_companies": ["SpamCorp"],
    "skip_already_applied": true,
    "max_daily_apply": 50
  },
  "profile": {
    "skills": ["Python", "Django", "React"],
    "headline": "Python Full Stack Developer | Django | React",
    "auto_refresh_daily": true
  }
}
```

---

## Code Flow — How It All Works (Read in This Order)

### Entry Point: `main.py`
```
User runs: python main.py --visible apply
                │
                ▼
        main.py (argparse)
                │
        Parses --visible flag and "apply" subcommand
                │
        Calls cmd_apply(args)
```
- `main.py` is the starting point — read this first
- Uses `argparse` to parse commands: login, apply, update, status, export
- The `--visible` flag controls headless vs visible browser
- Each command maps to a function: `cmd_login()`, `cmd_apply()`, `cmd_update()`, etc.

---

### Flow 1: `python main.py login`
```
main.py → cmd_login()
    │
    ├── browser.py → create_driver()
    │       Creates Chrome browser with anti-detection
    │       Auto-detects Chrome version for correct ChromeDriver
    │
    └── auth.py → login(driver)
            │
            ├── Step 1: Try load_cookies() from data/cookies.pkl
            │       If cookies exist → load them → check is_logged_in()
            │       If logged in → done!
            │
            └── Step 2: Fresh login (if cookies failed)
                    ├── Read email/password from .env
                    ├── Go to naukri.com/nlogin/login
                    ├── Find #usernameField → type email (human_type)
                    ├── Find #passwordField → type password (human_type)
                    ├── Click "Login" button
                    ├── Wait 5-8 seconds
                    ├── is_logged_in() → checks if redirected to homepage
                    └── save_cookies() → pickle cookies to data/cookies.pkl
```

**Key files to read:** `main.py:28-38` → `browser.py` → `auth.py`

---

### Flow 2: `python main.py apply`
```
main.py → cmd_apply()
    │
    ├── browser.py → create_driver()
    ├── auth.py → login(driver)           ← same as Flow 1
    │
    ├── search.py → search_jobs(driver, config)
    │       │
    │       ├── For each keyword in config.json → search.keywords:
    │       │       ├── _build_search_url() → builds naukri.com/python-developer-jobs-in-bangalore
    │       │       ├── driver.get(url)
    │       │       │
    │       │       └── For each page (1 to max_pages):
    │       │               ├── parse_job_listings(driver)
    │       │               │       Finds all job cards on page
    │       │               │       Extracts: title, company, location, link, job_id
    │       │               │
    │       │               └── paginate(driver) → click "Next" button
    │       │
    │       └── Deduplicate jobs by job_id
    │           Returns list of unique job dicts
    │
    └── apply.py → apply_to_jobs(driver, jobs, config)
            │
            └── For each job in the list:
                    ├── Check: already applied? (tracker.py → is_already_applied)
                    ├── Check: company blacklisted? (config.json → filters.blacklist_companies)
                    ├── Check: daily limit reached? (config.json → filters.max_daily_apply)
                    │
                    ├── _apply_single_job(driver, job)
                    │       ├── Go to job link
                    │       ├── Find "Apply" button
                    │       ├── Click it
                    │       └── handle_apply_flow(driver)
                    │               ├── Handle chatbot/questionnaire modal
                    │               ├── Check "already applied" message
                    │               └── Check success confirmation
                    │
                    ├── If success → tracker.py → save_applied(job)
                    │       Saves to data/applied.json with date, status
                    │
                    └── random_delay(3-6 seconds) before next job
```

**Key files to read:** `main.py:41-63` → `search.py` → `apply.py` → `tracker.py`

---

### Flow 3: `python main.py update`
```
main.py → cmd_update()
    │
    ├── browser.py → create_driver()
    ├── auth.py → login(driver)
    │
    └── profile.py
            ├── update_skills(driver, skills_list)
            │       Go to profile → click edit on Key Skills
            │       Type each skill + Enter
            │       Click Save
            │
            ├── update_resume_headline(driver, headline)
            │       Go to profile → click edit on Resume Headline
            │       Clear → type new headline
            │       Click Save
            │
            └── refresh_profile(driver)
                    Go to profile → edit headline
                    Toggle trailing space (add/remove)
                    Save → triggers Naukri's "profile updated" boost
```

**Key files to read:** `main.py:66-87` → `profile.py`

---

### Flow 4: `python main.py status` / `export`
```
main.py → cmd_status()                   main.py → cmd_export()
    │                                        │
    └── tracker.py → get_stats()             └── tracker.py → export_csv()
            Reads data/applied.json                  Reads data/applied.json
            Counts: total, today, by company         Writes CSV file
            Displays rich table                      Returns file path
```

**Key files to read:** `main.py:89-105` → `tracker.py`

---

### Utility Layer: `src/utils.py` (Used Everywhere)
```
random_delay(min, max)    → Sleep random seconds (anti-detection)
human_type(element, text) → Type character by character with random delays
random_scroll(driver)     → Scroll random pixels on page
setup_logger()            → File logger (logs/app.log) + colored console output
log_info/warn/error(msg)  → Print colored message + write to log file
```

---

## File Reading Order (For Learning)

Start here and follow this order to understand the full codebase:

1. **`config.json`** — Understand what settings drive the tool
2. **`main.py`** — Entry point, see how commands are wired up
3. **`src/utils.py`** — Helper functions used everywhere
4. **`src/browser.py`** — How the browser is created (short file)
5. **`src/auth.py`** — Login flow with cookie management
6. **`src/search.py`** — How jobs are searched and parsed from Naukri
7. **`src/apply.py`** — The core auto-apply engine
8. **`src/tracker.py`** — How applied jobs are stored and exported
9. **`src/profile.py`** — Profile update and refresh logic

---

## Anti-Detection Measures
- `undetected-chromedriver` patches Chrome to avoid bot detection
- Random delays (2-5s) between every action
- Human-like typing with character-by-character input
- Randomized scroll before clicking
- Cookie-based sessions to minimize login frequency
- Daily apply cap (default 50) to avoid account flags
- Auto-detects Chrome version to download matching ChromeDriver

## What Might Need Adjustment
- CSS selectors in auth.py, profile.py, search.py, apply.py may need updating as Naukri changes its DOM
- The chatbot/questionnaire handling in apply.py is basic — complex questionnaires may need manual intervention
- Chrome version compatibility with undetected-chromedriver
- If `distutils` error on Python 3.12+, install `setuptools` in the venv
