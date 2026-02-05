"""
Analysis module for job descriptions and resumes.

Exports:
    JobAnalyzer: Analyzes job descriptions and calculates match scores
    JobAnalysis: Dataclass for structured job analysis results
    ATSScorer: Scores resumes for ATS compatibility
    ATSScore: Dataclass for ATS scoring results
    generate_report: Generate human-readable ATS score report
"""

from .job_analyzer import JobAnalyzer, JobAnalysis, JobRequirement
from .ats_scorer import ATSScorer, ATSScore, generate_report

__all__ = [
    "JobAnalyzer",
    "JobAnalysis",
    "JobRequirement",
    "ATSScorer",
    "ATSScore",
    "generate_report",
]
