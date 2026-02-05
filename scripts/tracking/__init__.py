"""
Application tracking module.

Exports:
    ApplicationTracker: Manages application tracking database
    Application: Dataclass representing a job application
"""

from .tracker import ApplicationTracker, Application

__all__ = [
    "ApplicationTracker",
    "Application",
]
