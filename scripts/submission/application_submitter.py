"""
Application Submission Module
Automates job application submission using Playwright.

Supports two modes:
1. Standalone: Uses Playwright Python library directly
2. MCP mode: Returns instructions for Claude to execute via Playwright MCP
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Configuration
APPLIED_DIR = Path("jobs/applied")
CONFIG_DIR = Path("config")
RESUME_DIR = Path("resume")
SCREENSHOTS_DIR = Path("screenshots")

# Try to import Playwright
try:
    from playwright.sync_api import Locator, Page, sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def load_profile() -> dict[str, Any]:
    """Load user profile for form filling."""
    profile_path = CONFIG_DIR / "master_profile.yaml"
    if profile_path.exists():
        import yaml

        with open(profile_path) as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return data
    return {}


def get_resume_variant(job_id: str) -> Path | None:
    """Get the resume variant for a specific job."""
    variants_dir = RESUME_DIR / "variants"

    # Look for matching variant
    for variant in variants_dir.glob(f"*{job_id}*.pdf"):
        return variant

    # Fall back to latest approved variant
    approved_dir = RESUME_DIR / "variants" / "approved"
    if approved_dir.exists():
        variants = list(approved_dir.glob("*.pdf"))
        if variants:
            return max(variants, key=lambda p: p.stat().st_mtime)

    # Fall back to base export
    exports_dir = RESUME_DIR / "exports"
    if exports_dir.exists():
        exports = list(exports_dir.glob("*.pdf"))
        if exports:
            return max(exports, key=lambda p: p.stat().st_mtime)

    return None


def validate_submission(job: dict, resume_path: Path) -> dict:
    """
    Validate submission requirements before applying.

    Returns dict with 'valid' boolean and 'errors' list.
    """
    errors = []

    # Check resume exists and is valid
    if not resume_path or not resume_path.exists():
        errors.append("Resume variant not found")
    elif resume_path.stat().st_size < 1000:
        errors.append("Resume file appears corrupt (too small)")

    # Check ATS score if available
    ats_score = job.get("ats_score", 0)
    if ats_score < 70:
        errors.append(f"ATS score too low: {ats_score}% (minimum 70%)")

    # Check match score
    match_score = job.get("match_score", 0)
    if match_score < 70:
        errors.append(f"Match score too low: {match_score}% (minimum 70%)")

    # Check not already applied (DB lookup)
    try:
        from scripts.tracking import ApplicationTracker

        tracker = ApplicationTracker()
        company = job.get("company", "")
        role = job.get("title") or job.get("role", "")
        job_url = job.get("job_url") or job.get("url")
        existing = tracker.is_already_applied(company, role, job_url)
        if existing:
            errors.append(
                f"Already applied to this position "
                f"(id={existing['id']}, status={existing['status']})"
            )
    except Exception:
        # Fall back to simple status check if tracker unavailable
        if job.get("status") == "applied":
            errors.append("Already applied to this position")

    return {"valid": len(errors) == 0, "errors": errors}


def submit_application(
    job: dict, resume_path: Path, cover_letter_path: Path | None = None, confirm: bool = True
) -> dict:
    """
    Submit job application using Playwright automation.

    This function is designed to work with Playwright MCP server.
    When called from Claude Code, use the playwright MCP tools directly.

    Args:
        job: Job dictionary with application URL
        resume_path: Path to resume PDF
        cover_letter_path: Optional cover letter path
        confirm: Whether to require confirmation before submit

    Returns:
        Submission result dictionary
    """
    # Validate first
    validation = validate_submission(job, resume_path)
    if not validation["valid"]:
        return {"status": "validation_failed", "errors": validation["errors"]}

    # Load profile for form filling
    profile = load_profile()
    personal = profile.get("personal", {})

    application_url = job.get("application_url") or job.get("job_url")
    if not application_url:
        return {"status": "error", "message": "No application URL found"}

    # Prepare submission data
    submission_data = {
        "url": application_url,
        "company": job.get("company", "Unknown"),
        "title": job.get("title", "Unknown"),
        "resume_path": str(resume_path),
        "cover_letter_path": str(cover_letter_path) if cover_letter_path else None,
        "form_data": _extract_form_data(personal),
        "job_id": job.get("id"),
        "timestamp": datetime.now().isoformat(),
    }

    if not confirm:
        return {
            "status": "awaiting_confirmation",
            "message": "Review submission data and confirm to proceed",
            "submission_data": submission_data,
        }

    # Try Playwright automation if available
    if PLAYWRIGHT_AVAILABLE:
        try:
            result = execute_playwright_submission(submission_data)
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Playwright automation failed: {str(e)}",
                "submission_data": submission_data,
                "fallback": "Use MCP mode or manual submission",
            }

    # Fallback: Return instructions for Claude to execute via Playwright MCP
    return {
        "status": "ready_to_submit",
        "message": "Playwright not available. Use MCP tools to complete submission.",
        "mcp_instructions": {
            "tools": [
                {"tool": "browser_navigate", "params": {"url": application_url}},
                {"tool": "browser_snapshot", "params": {}},
                {
                    "tool": "browser_fill_form",
                    "params": {"fields": _map_form_fields(submission_data["form_data"])},
                },
                {"tool": "browser_file_upload", "params": {"paths": [str(resume_path)]}},
                {"tool": "browser_click", "params": {"element": "Submit button"}},
                {"tool": "browser_take_screenshot", "params": {"type": "png"}},
            ]
        },
        "submission_data": submission_data,
    }


def _extract_form_data(personal: dict) -> dict[str, str]:
    """Extract form data from profile, handling both flat and nested structures."""

    def _get(key: str, *nested_keys: str) -> str:
        val = personal.get(key, "")
        if isinstance(val, dict):
            for nk in nested_keys:
                val = val.get(nk, "")
                if not isinstance(val, dict):
                    break
        return str(val) if val else ""

    return {
        "name": _get("name", "full"),
        "email": _get("email") or _get("contact", "email"),
        "phone": _get("phone") or _get("contact", "phone"),
        "linkedin": _get("linkedin") or _get("social", "linkedin"),
        "website": _get("website") or _get("social", "website"),
        "location": _get("location"),
    }


def _map_form_fields(form_data: dict) -> list[dict[str, Any]]:
    """Map form data to Playwright MCP fill_form format."""
    field_mapping = {
        "name": {"type": "textbox", "patterns": ["name", "full name", "your name"]},
        "email": {"type": "textbox", "patterns": ["email", "e-mail"]},
        "phone": {"type": "textbox", "patterns": ["phone", "mobile", "telephone"]},
        "linkedin": {"type": "textbox", "patterns": ["linkedin", "profile url"]},
        "website": {"type": "textbox", "patterns": ["website", "portfolio"]},
        "location": {"type": "textbox", "patterns": ["location", "city", "address"]},
    }

    fields = []
    for key, value in form_data.items():
        if value and key in field_mapping:
            fields.append(
                {
                    "name": key,
                    "type": field_mapping[key]["type"],
                    "value": value,
                    "patterns": field_mapping[key]["patterns"],
                }
            )
    return fields


def execute_playwright_submission(submission_data: dict) -> dict:
    """
    Execute job application using Playwright Python library.

    Args:
        submission_data: Dict with url, form_data, resume_path

    Returns:
        Submission result with status and screenshot path
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    company = submission_data.get("company", "unknown").replace(" ", "_").lower()
    screenshot_path = SCREENSHOTS_DIR / f"{company}_{timestamp}.png"

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Visible for human oversight
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to application page
            page.goto(submission_data["url"], timeout=30000)
            page.wait_for_load_state("networkidle")

            # Try to fill form fields
            form_data = submission_data.get("form_data", {})
            filled_fields = _fill_application_form(page, form_data)

            # Upload resume
            resume_path = submission_data.get("resume_path")
            uploaded = _upload_resume(page, resume_path) if resume_path else False

            # Take screenshot before submission
            page.screenshot(path=str(screenshot_path))

            # Look for submit button but DON'T click - human review required
            submit_button = _find_submit_button(page)

            return {
                "status": "ready_for_review",
                "message": "Form filled. Review and click submit manually.",
                "screenshot": str(screenshot_path),
                "filled_fields": filled_fields,
                "resume_uploaded": uploaded,
                "submit_button_found": submit_button is not None,
                "browser_open": True,  # Browser stays open for human review
            }

        except Exception as e:
            page.screenshot(path=str(screenshot_path))
            browser.close()
            raise e


def _fill_application_form(page: Page, form_data: dict) -> list[str]:
    """Fill form fields on the page."""
    filled = []

    # Common field selectors
    field_selectors = {
        "name": ['input[name*="name" i]', 'input[placeholder*="name" i]', "#name", "#fullName"],
        "email": ['input[type="email"]', 'input[name*="email" i]', "#email"],
        "phone": [
            'input[type="tel"]',
            'input[name*="phone" i]',
            'input[name*="mobile" i]',
            "#phone",
        ],
        "linkedin": ['input[name*="linkedin" i]', 'input[placeholder*="linkedin" i]'],
        "website": ['input[name*="website" i]', 'input[name*="portfolio" i]'],
        "location": [
            'input[name*="location" i]',
            'input[name*="city" i]',
            'input[name*="address" i]',
        ],
    }

    for field_name, value in form_data.items():
        if not value or field_name not in field_selectors:
            continue

        for selector in field_selectors[field_name]:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    element.fill(value)
                    filled.append(field_name)
                    break
            except Exception:
                continue

    # Second pass: use AnswerResolver for remaining unfilled fields
    try:
        from scripts.submission.easy_apply_answers import AnswerResolver

        resolver = AnswerResolver.from_profile()
        unfilled = _extract_unfilled_labels(page, filled)

        for label_text, element_info in unfilled:
            resolved = resolver.resolve(
                question=label_text,
                field_type=element_info.get("type", "text"),
                options=element_info.get("options"),
            )
            if resolved and resolved.confidence >= 0.7:
                try:
                    el = element_info.get("element")
                    if el and el.is_visible():
                        if resolved.field_type in ("dropdown", "select"):
                            el.select_option(label=resolved.answer)
                        else:
                            el.fill(resolved.answer)
                        filled.append(f"auto:{label_text[:30]}")
                except Exception:
                    continue
    except ImportError:
        pass  # AnswerResolver not available

    return filled


def _extract_unfilled_labels(
    page: Page, already_filled: list[str]
) -> list[tuple[str, dict[str, Any]]]:
    """
    Extract labels and their associated input elements for unfilled fields.

    Returns list of (label_text, {"element": locator, "type": str, "options": list|None})
    """
    results = []

    try:
        # Find all label elements
        labels = page.locator("label").all()
        for label in labels:
            try:
                label_text = label.inner_text().strip()
                if not label_text or len(label_text) > 200:
                    continue

                # Skip if this field was already filled
                if any(f.lower() in label_text.lower() for f in already_filled):
                    continue

                # Find associated input
                for_attr = label.get_attribute("for")
                if for_attr:
                    input_el = page.locator(f"#{for_attr}").first
                else:
                    input_el = label.locator("input, select, textarea").first

                if not input_el or not input_el.is_visible():
                    continue

                tag = input_el.evaluate("el => el.tagName.toLowerCase()")
                input_type = input_el.get_attribute("type") or "text"

                element_info: dict[str, Any] = {"element": input_el, "type": input_type}

                if tag == "select":
                    element_info["type"] = "dropdown"
                    option_els = input_el.locator("option").all()
                    element_info["options"] = [
                        o.inner_text().strip() for o in option_els if o.inner_text().strip()
                    ]

                results.append((label_text, element_info))
            except Exception:
                continue
    except Exception:
        pass  # Best-effort extraction; return whatever was collected

    return results


def _upload_resume(page: Page, resume_path: str) -> bool:
    """Upload resume file."""
    try:
        # Common file input selectors
        file_selectors = [
            'input[type="file"]',
            'input[accept*="pdf"]',
            'input[name*="resume" i]',
            'input[name*="cv" i]',
        ]

        for selector in file_selectors:
            try:
                file_input = page.locator(selector).first
                if file_input:
                    file_input.set_input_files(resume_path)
                    return True
            except Exception:
                continue

        return False
    except Exception:
        return False


def _find_submit_button(page: Page) -> Locator | None:
    """Find the submit button on the page."""
    submit_selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
        'button:has-text("Send")',
        'a:has-text("Submit Application")',
    ]

    for selector in submit_selectors:
        try:
            button = page.locator(selector).first
            if button.is_visible():
                return button
        except Exception:
            continue

    return None


def record_application(job: dict, result: dict) -> Path:
    """Save application record."""
    APPLIED_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = job.get("id", "unknown")
    company = job.get("company", "unknown").replace(" ", "_").lower()

    filename = f"{company}_{job_id}_{timestamp}.json"
    filepath = APPLIED_DIR / filename

    record = {"job": job, "result": result, "timestamp": timestamp, "status": result.get("status")}

    with open(filepath, "w") as f:
        json.dump(record, f, indent=2)

    return filepath


def apply_to_job(job_id: str, confirm: bool = False) -> dict:
    """
    Main entry point for job application.

    Args:
        job_id: ID of the job to apply to
        confirm: Whether to proceed without additional confirmation

    Returns:
        Application result
    """
    # Load job from analyzed
    analyzed_dir = Path("jobs/analyzed")
    job_files = list(analyzed_dir.glob(f"*{job_id}*.json"))

    if not job_files:
        return {"status": "error", "message": f"Job {job_id} not found"}

    with open(job_files[0]) as f:
        job = json.load(f)

    # Get resume
    resume_path = get_resume_variant(job_id)
    if not resume_path:
        return {"status": "error", "message": "No resume variant found"}

    # Submit
    result = submit_application(job, resume_path, confirm=confirm)

    # Record any successful submission attempt
    if result.get("status") in ("submitted", "ready_for_review", "ready_to_submit"):
        record_path = record_application(job, result)
        result["record_path"] = str(record_path)

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python application_submitter.py <job_id> [--confirm]")
        sys.exit(1)

    job_id = sys.argv[1]
    confirm = "--confirm" in sys.argv

    result = apply_to_job(job_id, confirm)
    print(json.dumps(result, indent=2))
