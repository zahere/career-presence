"""
Application submission module.

Exports:
    apply_to_job: Main entry point for job application
    submit_application: Submit job application using Playwright automation
    validate_submission: Validate submission requirements before applying
    get_resume_variant: Get the resume variant for a specific job
    record_application: Save application record
"""

from .application_submitter import (
    apply_to_job,
    submit_application,
    validate_submission,
    get_resume_variant,
    record_application,
)

__all__ = [
    "apply_to_job",
    "submit_application",
    "validate_submission",
    "get_resume_variant",
    "record_application",
]
