"""
Application submission module.

Exports:
    apply_to_job: Main entry point for job application
    submit_application: Submit job application using Playwright automation
    validate_submission: Validate submission requirements before applying
    get_resume_variant: Get the resume variant for a specific job
    record_application: Save application record
    AnswerResolver: Resolves Easy Apply questions from master profile
"""

from .application_submitter import (
    apply_to_job,
    get_resume_variant,
    record_application,
    submit_application,
    validate_submission,
)
from .easy_apply_answers import AnswerResolver

__all__ = [
    "apply_to_job",
    "submit_application",
    "validate_submission",
    "get_resume_variant",
    "record_application",
    "AnswerResolver",
]
