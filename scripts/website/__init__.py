"""
Website generation module.

Exports:
    WebsiteGenerator: Generates portfolio website from master profile data
    WebsiteConfig: Dataclass for website generation configuration
"""

from .generator import WebsiteConfig, WebsiteGenerator

__all__ = [
    "WebsiteGenerator",
    "WebsiteConfig",
]
