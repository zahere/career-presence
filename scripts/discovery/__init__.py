"""
Job discovery module for multi-platform job search.

Exports:
    search_jobs: Main function to search for jobs across platforms
    load_targets: Load target companies and search parameters from config
    apply_targets_filter: Filter and enrich jobs based on targets.yaml
    deduplicate_jobs: Remove duplicate job postings
    print_summary: Print formatted summary of search results
"""

from .job_searcher import (
    _merge_locale,
    apply_targets_filter,
    deduplicate_jobs,
    load_targets,
    print_summary,
    search_jobs,
)

__all__ = [
    "search_jobs",
    "load_targets",
    "apply_targets_filter",
    "deduplicate_jobs",
    "print_summary",
    "_merge_locale",
]
