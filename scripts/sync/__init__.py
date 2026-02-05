"""
Platform synchronization module.

Exports:
    PlatformSyncManager: Manages sync across all career platforms
    Platform: Enum of supported platforms (resume, linkedin, github, website)
    SyncResult: Dataclass for sync operation results
"""

from .sync_manager import Platform, PlatformSyncManager, SyncResult

__all__ = [
    "PlatformSyncManager",
    "Platform",
    "SyncResult",
]
