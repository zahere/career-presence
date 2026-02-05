"""
Config validation module.

Exports:
    TargetsConfig: Pydantic model for targets.yaml
    MasterProfileConfig: Pydantic model for master_profile.yaml
    load_validated_targets: Load and validate targets.yaml
    load_validated_profile: Load and validate master_profile.yaml
    validate_all_configs: Validate all config files
"""

from .config_validator import (
    MasterProfileConfig,
    TargetsConfig,
    load_validated_profile,
    load_validated_targets,
    validate_all_configs,
)

__all__ = [
    "TargetsConfig",
    "MasterProfileConfig",
    "load_validated_targets",
    "load_validated_profile",
    "validate_all_configs",
]
