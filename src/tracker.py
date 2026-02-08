import csv
import json
import os
from collections import Counter
from datetime import date

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
APPLIED_FILE = os.path.join(DATA_DIR, "applied.json")


def load_applied():
    """Read applied jobs from JSON file."""
    if not os.path.exists(APPLIED_FILE):
        return []
    with open(APPLIED_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_applied(job):
    """Append a single applied job to the JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    applied = load_applied()
    applied.append(job)
    with open(APPLIED_FILE, "w", encoding="utf-8") as f:
        json.dump(applied, f, indent=2, ensure_ascii=False)


def is_already_applied(job_id):
    """Check if a job has already been applied to."""
    if not job_id:
        return False
    applied = load_applied()
    return any(j.get("job_id") == job_id for j in applied)


def get_stats():
    """Return summary statistics about applied jobs."""
    applied = load_applied()
    today = str(date.today())

    total = len(applied)
    today_count = sum(1 for j in applied if j.get("date") == today)
    companies = Counter(j.get("company", "Unknown") for j in applied)

    return {
        "total": total,
        "today": today_count,
        "by_company": dict(companies.most_common(20)),
    }


def export_csv(output_path=None):
    """Export applied jobs to a CSV file."""
    applied = load_applied()
    if not applied:
        return None

    if output_path is None:
        output_path = os.path.join(DATA_DIR, "applied_jobs.csv")

    fieldnames = ["job_id", "title", "company", "location", "link", "date", "status"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(applied)

    return output_path
