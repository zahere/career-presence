"""
Job discovery module for multi-platform job search.

Exports:
    search_jobs: Main function to search for jobs across platforms
    load_targets: Load target companies and search parameters from config
    deduplicate_jobs: Remove duplicate job postings
    print_summary: Print formatted summary of search results
"""

from .job_searcher import search_jobs, load_targets, deduplicate_jobs, print_summary

__all__ = [
    "search_jobs",
    "load_targets",
    "deduplicate_jobs",
    "print_summary",
]
