"""
Resume tailoring module.

Exports:
    ResumeTailor: Generates tailored resume variants from base LaTeX resume
    ResumeVariant: Dataclass representing a tailored resume variant
"""

from .resume_tailor import ResumeTailor, ResumeVariant

__all__ = [
    "ResumeTailor",
    "ResumeVariant",
]
