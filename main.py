#!/usr/bin/env python3
"""Naukri.com Auto-Apply Tool — CLI Entry Point."""

import argparse
import json
import os
import sys

from rich.console import Console
from rich.table import Table

from src.auth import login
from src.browser import create_driver
from src.profile import refresh_profile, update_resume_headline, update_skills
from src.search import search_jobs
from src.apply import apply_to_jobs
from src.tracker import export_csv, get_stats
from src.utils import log_error, log_info, setup_logger

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
console = Console()


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def cmd_login(args):
    """Login to Naukri and save session cookies."""
    setup_logger()
    driver = create_driver(headless=not args.visible)
    try:
        if login(driver):
            log_info("Login complete — session saved")
        else:
            log_error("Login failed")
            sys.exit(1)
    finally:
        driver.quit()


def cmd_apply(args):
    """Run full search + apply cycle."""
    setup_logger()
    config = load_config()
    driver = create_driver(headless=not args.visible)
    try:
        if not login(driver):
            log_error("Cannot apply — login failed")
            sys.exit(1)

        log_info("Searching for jobs...")
        jobs = search_jobs(driver, config, max_pages=args.pages)

        if not jobs:
            log_info("No jobs found matching your criteria")
            return

        log_info(f"Found {len(jobs)} jobs — starting apply cycle")
        results = apply_to_jobs(driver, jobs, config)

        console.print(f"\n[bold green]Applied:[/] {results['applied']}")
        console.print(f"[bold yellow]Skipped:[/] {results['skipped']}")
        console.print(f"[bold red]Failed:[/] {results['failed']}")
    finally:
        driver.quit()


def cmd_update(args):
    """Update profile skills and refresh profile."""
    setup_logger()
    config = load_config()
    driver = create_driver(headless=not args.visible)
    try:
        if not login(driver):
            log_error("Cannot update profile — login failed")
            sys.exit(1)

        profile_cfg = config.get("profile", {})

        skills = profile_cfg.get("skills", [])
        if skills:
            update_skills(driver, skills)

        headline = profile_cfg.get("headline", "")
        if headline:
            update_resume_headline(driver, headline)

        if profile_cfg.get("auto_refresh_daily", False):
            refresh_profile(driver)

        log_info("Profile update complete")
    finally:
        driver.quit()


def cmd_status(args):
    """Show applied jobs statistics."""
    stats = get_stats()

    console.print(f"\n[bold]Naukri Auto-Apply Stats[/]\n")
    console.print(f"  Total applied: [bold green]{stats['total']}[/]")
    console.print(f"  Applied today: [bold cyan]{stats['today']}[/]\n")

    if stats["by_company"]:
        table = Table(title="Applications by Company")
        table.add_column("Company", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for company, count in stats["by_company"].items():
            table.add_row(company, str(count))

        console.print(table)
    else:
        console.print("  No applications recorded yet.")


def cmd_export(args):
    """Export applied jobs to CSV."""
    output = args.output or None
    path = export_csv(output)
    if path:
        log_info(f"Exported to: {path}")
    else:
        log_info("No applications to export")


def main():
    parser = argparse.ArgumentParser(
        description="Naukri.com Auto-Apply Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--visible", action="store_true", help="Run browser in visible (non-headless) mode")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # login
    subparsers.add_parser("login", help="Login to Naukri and save session")

    # apply
    apply_parser = subparsers.add_parser("apply", help="Search and auto-apply to jobs")
    apply_parser.add_argument("--pages", type=int, default=3, help="Max search result pages per keyword (default: 3)")

    # update
    subparsers.add_parser("update", help="Update profile skills and refresh")

    # status
    subparsers.add_parser("status", help="Show applied jobs statistics")

    # export
    export_parser = subparsers.add_parser("export", help="Export applied jobs to CSV")
    export_parser.add_argument("--output", "-o", help="Output CSV file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "login": cmd_login,
        "apply": cmd_apply,
        "update": cmd_update,
        "status": cmd_status,
        "export": cmd_export,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
