"""
LinkedIn content management module.

Exports:
    LinkedInContentManager: Manages LinkedIn content creation and scheduling
    LinkedInPost: Dataclass representing a LinkedIn post
    PostType: Enum of post types (technical_insight, build_in_public, etc.)
"""

from .linkedin_manager import LinkedInContentManager, LinkedInPost, PostType

__all__ = [
    "LinkedInContentManager",
    "LinkedInPost",
    "PostType",
]
