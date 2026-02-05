"""
Application Submission Module
Automates job application submission using Playwright MCP.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuration
APPLIED_DIR = Path("jobs/applied")
CONFIG_DIR = Path("config")
RESUME_DIR = Path("resume")


def load_profile() -> dict:
    """Load user profile for form filling."""
    profile_path = CONFIG_DIR / "master_profile.yaml"
    if profile_path.exists():
        import yaml
        with open(profile_path) as f:
            return yaml.safe_load(f)
    return {}


def get_resume_variant(job_id: str) -> Optional[Path]:
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

    # Check not already applied
    if job.get("status") == "applied":
        errors.append("Already applied to this position")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def submit_application(
    job: dict,
    resume_path: Path,
    cover_letter_path: Optional[Path] = None,
    confirm: bool = True
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
        return {
            "status": "validation_failed",
            "errors": validation["errors"]
        }

    # Placeholder - actual implementation uses MCP
    print(f"Would submit application to: {job.get('company')} - {job.get('title')}")
    print(f"URL: {job.get('application_url')}")
    print(f"Resume: {resume_path}")

    if confirm:
        print("Confirmation required - use --confirm flag to proceed")
        return {"status": "awaiting_confirmation"}

    return {
        "status": "submitted",
        "job_id": job.get("id"),
        "timestamp": datetime.now().isoformat()
    }


def record_application(job: dict, result: dict) -> Path:
    """Save application record."""
    APPLIED_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = job.get("id", "unknown")
    company = job.get("company", "unknown").replace(" ", "_").lower()

    filename = f"{company}_{job_id}_{timestamp}.json"
    filepath = APPLIED_DIR / filename

    record = {
        "job": job,
        "result": result,
        "timestamp": timestamp,
        "status": result.get("status")
    }

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

    # Record
    if result.get("status") == "submitted":
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
