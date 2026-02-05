"""
Config Validation Layer

Pydantic v2 models for validating targets.yaml and master_profile.yaml.
Provides typed access and early error detection for all configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


# ═══════════════════════════════════════════════════════════════════════════
# targets.yaml models
# ═══════════════════════════════════════════════════════════════════════════


class CompanyEntry(BaseModel):
    name: str
    careers_url: str | None = None
    greenhouse_id: str | None = None
    lever_id: str | None = None
    ashby_id: str | None = None
    priority: int = 3
    notes: str | None = None


class TierConfig(BaseModel):
    companies: list[CompanyEntry] = Field(default_factory=list)


class ExclusionsConfig(BaseModel):
    companies: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    reasons: dict[str, str] | None = None


class TargetRolesConfig(BaseModel):
    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)


class LocationConfig(BaseModel):
    preferred: list[str] = Field(default_factory=list)
    acceptable: list[str] = Field(default_factory=list)


class SalaryConfig(BaseModel):
    minimum_usd: int = 0
    currency: str = "USD"


class SearchParamsConfig(BaseModel):
    locations: LocationConfig = Field(default_factory=LocationConfig)
    experience_levels: list[str] = Field(default_factory=list)
    job_types: list[str] = Field(default_factory=list)
    posted_within: str = "7d"
    salary: SalaryConfig = Field(default_factory=SalaryConfig)
    country: str = "USA"


class BadWordsConfig(BaseModel):
    title_words: list[str] = Field(default_factory=list)
    description_words: list[str] = Field(default_factory=list)
    penalty_per_match: float = 5.0


class ExperienceRangeConfig(BaseModel):
    min_years: int = 0
    max_years: int = 50


class LocaleSalaryConfig(BaseModel):
    """Locale-specific salary config that may use non-USD fields."""

    currency: str = "USD"
    model_config = {"extra": "allow"}


class LocaleSearchParamsConfig(BaseModel):
    """Partial search params for locale overrides (all fields optional)."""

    locations: LocationConfig | None = None
    country: str | None = None
    salary: LocaleSalaryConfig | None = None


class LocaleConfig(BaseModel):
    """Region-specific overrides merged into the base targets config."""

    search_params: LocaleSearchParamsConfig | None = None
    tiers: dict[str, TierConfig] = Field(default_factory=dict)
    bad_words: BadWordsConfig | None = None


class TargetsConfig(BaseModel):
    version: str = "1.0"
    last_updated: str | None = None
    tiers: dict[str, TierConfig] = Field(default_factory=dict)
    exclusions: ExclusionsConfig = Field(default_factory=ExclusionsConfig)
    target_roles: TargetRolesConfig = Field(default_factory=TargetRolesConfig)
    search_params: SearchParamsConfig = Field(default_factory=SearchParamsConfig)
    bad_words: BadWordsConfig = Field(default_factory=BadWordsConfig)
    experience_range: ExperienceRangeConfig = Field(default_factory=ExperienceRangeConfig)
    locales: dict[str, LocaleConfig] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _normalize_tiers(cls, data: Any) -> Any:
        """Convert raw tier dicts to TierConfig objects."""
        if isinstance(data, dict) and "tiers" in data:
            tiers = data["tiers"]
            for key, value in tiers.items():
                if isinstance(value, dict) and "companies" not in value:
                    # Handle unexpected tier format
                    tiers[key] = {"companies": []}
        return data

    def get_all_companies(self) -> list[CompanyEntry]:
        """Get all companies across all tiers."""
        companies = []
        for tier in self.tiers.values():
            companies.extend(tier.companies)
        return companies

    def get_company_tier(self, company_name: str) -> str | None:
        """Look up which tier a company belongs to."""
        name_lower = company_name.lower()
        for tier_name, tier in self.tiers.items():
            for company in tier.companies:
                if company.name.lower() == name_lower:
                    return tier_name
        return None


# ═══════════════════════════════════════════════════════════════════════════
# master_profile.yaml models
# ═══════════════════════════════════════════════════════════════════════════


class NameConfig(BaseModel):
    full: str = ""
    first: str = ""
    last: str = ""


class ContactConfig(BaseModel):
    email: str = ""
    phone: str = ""
    location: str = ""
    timezone: str = ""


class SocialConfig(BaseModel):
    linkedin: str = ""
    github: str = ""
    twitter: str = ""
    website: str = ""


class PersonalConfig(BaseModel):
    name: NameConfig = Field(default_factory=NameConfig)
    tagline: str = ""
    headlines: dict[str, str] = Field(default_factory=dict)
    contact: ContactConfig = Field(default_factory=ContactConfig)
    social: SocialConfig = Field(default_factory=SocialConfig)
    languages: list[dict[str, str]] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    id: str = ""
    company: str = ""
    role: str = ""
    type: str = ""
    location: str = ""
    start_date: str | None = None
    end_date: str | None = None
    short_description: str = ""
    bullets: list[dict[str, Any]] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class SkillEntry(BaseModel):
    name: str
    proficiency: str = "familiar"
    years: int = 0


class SkillCategory(BaseModel):
    name: str
    skills: list[SkillEntry] = Field(default_factory=list)


class LinkedInSkills(BaseModel):
    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)


class SkillsConfig(BaseModel):
    categories: list[SkillCategory] = Field(default_factory=list)
    linkedin_skills: LinkedInSkills = Field(default_factory=LinkedInSkills)


class ApplicationAnswersConfig(BaseModel):
    work_authorization: str = ""
    visa_sponsorship: str = ""
    years_of_experience: str = ""
    education_level: str = ""
    salary_expectation: str = ""
    start_date: str = ""
    willing_to_relocate: str = ""
    custom_answers: dict[str, str] = Field(default_factory=dict)


class MasterProfileConfig(BaseModel):
    version: str = "1.0"
    last_updated: str | None = None
    personal: PersonalConfig = Field(default_factory=PersonalConfig)
    summaries: dict[str, str] = Field(default_factory=dict)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    education: list[dict[str, Any]] = Field(default_factory=list)
    content_strategy: dict[str, Any] = Field(default_factory=dict)
    sync: dict[str, Any] = Field(default_factory=dict)
    application_answers: ApplicationAnswersConfig = Field(default_factory=ApplicationAnswersConfig)


# ═══════════════════════════════════════════════════════════════════════════
# Loader functions
# ═══════════════════════════════════════════════════════════════════════════


def load_validated_targets(path: Path | None = None) -> TargetsConfig:
    """Load and validate targets.yaml, returning a typed TargetsConfig."""
    path = path or CONFIG_DIR / "targets.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Targets config not found: {path}")
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    return TargetsConfig.model_validate(raw)


def load_validated_profile(path: Path | None = None) -> MasterProfileConfig:
    """Load and validate master_profile.yaml, returning a typed MasterProfileConfig."""
    path = path or CONFIG_DIR / "master_profile.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Master profile not found: {path}")
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    return MasterProfileConfig.model_validate(raw)


def validate_all_configs(
    targets_path: Path | None = None,
    profile_path: Path | None = None,
) -> dict[str, Any]:
    """
    Validate all config files and return a summary.

    Returns:
        {"valid": bool, "errors": [...], "warnings": [...]}
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Validate targets.yaml
    tp = targets_path or CONFIG_DIR / "targets.yaml"
    if tp.exists():
        try:
            targets = load_validated_targets(tp)
            all_companies = targets.get_all_companies()
            if not all_companies:
                warnings.append("targets.yaml: No companies configured in any tier")
            if not targets.target_roles.primary:
                warnings.append("targets.yaml: No primary target roles defined")
            if not targets.bad_words.title_words and not targets.bad_words.description_words:
                warnings.append("targets.yaml: No bad_words configured (filtering disabled)")
        except Exception as e:
            errors.append(f"targets.yaml: {e}")
    else:
        warnings.append(f"targets.yaml not found at {tp}")

    # Validate master_profile.yaml
    pp = profile_path or CONFIG_DIR / "master_profile.yaml"
    if pp.exists():
        try:
            profile = load_validated_profile(pp)
            if not profile.personal.contact.email:
                warnings.append("master_profile.yaml: No email configured")
            if not profile.experience:
                warnings.append("master_profile.yaml: No experience entries")
            if not profile.application_answers.work_authorization:
                warnings.append(
                    "master_profile.yaml: No application_answers configured "
                    "(Easy Apply question answering disabled)"
                )
        except Exception as e:
            errors.append(f"master_profile.yaml: {e}")
    else:
        warnings.append(f"master_profile.yaml not found at {pp}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
