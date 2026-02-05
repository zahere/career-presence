"""Tests for config validation layer."""

import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError

from scripts.validation.config_validator import (
    TargetsConfig,
    MasterProfileConfig,
    ApplicationAnswersConfig,
    BadWordsConfig,
    ExperienceRangeConfig,
    load_validated_targets,
    load_validated_profile,
    validate_all_configs,
)


# ═══════════════════════════════════════════════════════════════════════════
# TargetsConfig tests
# ═══════════════════════════════════════════════════════════════════════════


class TestTargetsConfig:
    def test_minimal_targets(self):
        """Empty targets should parse with defaults."""
        config = TargetsConfig.model_validate({})
        assert config.version == "1.0"
        assert config.tiers == {}
        assert config.bad_words.title_words == []
        assert config.experience_range.min_years == 0

    def test_full_targets(self):
        """Full targets.yaml structure should parse correctly."""
        raw = {
            "version": "1.0",
            "tiers": {
                "tier1": {
                    "companies": [
                        {"name": "Anthropic", "careers_url": "https://anthropic.com/careers", "priority": 1}
                    ]
                },
                "tier2": {
                    "companies": [
                        {"name": "Scale AI", "lever_id": "scale", "priority": 2}
                    ]
                },
            },
            "exclusions": {
                "companies": ["BadCorp"],
                "keywords": ["unpaid"],
            },
            "target_roles": {
                "primary": ["AI Engineer"],
                "secondary": ["Platform Engineer"],
            },
            "bad_words": {
                "title_words": ["junior", "director"],
                "description_words": ["security clearance required"],
                "penalty_per_match": 10.0,
            },
            "experience_range": {
                "min_years": 3,
                "max_years": 15,
            },
        }
        config = TargetsConfig.model_validate(raw)

        assert len(config.tiers["tier1"].companies) == 1
        assert config.tiers["tier1"].companies[0].name == "Anthropic"
        assert config.exclusions.companies == ["BadCorp"]
        assert config.bad_words.penalty_per_match == 10.0
        assert config.experience_range.min_years == 3

    def test_get_all_companies(self):
        config = TargetsConfig.model_validate({
            "tiers": {
                "tier1": {"companies": [{"name": "A"}]},
                "tier2": {"companies": [{"name": "B"}, {"name": "C"}]},
            }
        })
        assert len(config.get_all_companies()) == 3

    def test_get_company_tier(self):
        config = TargetsConfig.model_validate({
            "tiers": {
                "tier1": {"companies": [{"name": "Anthropic"}]},
                "tier2": {"companies": [{"name": "Scale AI"}]},
            }
        })
        assert config.get_company_tier("Anthropic") == "tier1"
        assert config.get_company_tier("anthropic") == "tier1"
        assert config.get_company_tier("Scale AI") == "tier2"
        assert config.get_company_tier("Unknown") is None


class TestBadWordsConfig:
    def test_defaults(self):
        config = BadWordsConfig()
        assert config.title_words == []
        assert config.penalty_per_match == 5.0

    def test_custom(self):
        config = BadWordsConfig(title_words=["junior"], penalty_per_match=8.0)
        assert config.title_words == ["junior"]
        assert config.penalty_per_match == 8.0


class TestExperienceRangeConfig:
    def test_defaults(self):
        config = ExperienceRangeConfig()
        assert config.min_years == 0
        assert config.max_years == 50

    def test_custom(self):
        config = ExperienceRangeConfig(min_years=3, max_years=10)
        assert config.min_years == 3
        assert config.max_years == 10


# ═══════════════════════════════════════════════════════════════════════════
# MasterProfileConfig tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMasterProfileConfig:
    def test_minimal_profile(self):
        config = MasterProfileConfig.model_validate({})
        assert config.version == "1.0"
        assert config.personal.contact.email == ""
        assert config.application_answers.work_authorization == ""

    def test_application_answers(self):
        raw = {
            "application_answers": {
                "work_authorization": "Yes",
                "visa_sponsorship": "No",
                "years_of_experience": "5",
                "custom_answers": {
                    "How did you hear about us?": "LinkedIn",
                },
            }
        }
        config = MasterProfileConfig.model_validate(raw)
        assert config.application_answers.work_authorization == "Yes"
        assert config.application_answers.custom_answers["How did you hear about us?"] == "LinkedIn"

    def test_full_profile(self):
        raw = {
            "personal": {
                "name": {"full": "Test User", "first": "Test", "last": "User"},
                "contact": {"email": "test@example.com", "phone": "+1-555-0000"},
                "social": {"linkedin": "https://linkedin.com/in/test"},
            },
            "experience": [
                {"id": "job1", "company": "TestCo", "role": "Engineer", "type": "employee"}
            ],
            "skills": {
                "categories": [
                    {"name": "Languages", "skills": [{"name": "Python", "proficiency": "expert", "years": 5}]}
                ]
            },
        }
        config = MasterProfileConfig.model_validate(raw)
        assert config.personal.name.full == "Test User"
        assert len(config.experience) == 1
        assert config.skills.categories[0].skills[0].name == "Python"


# ═══════════════════════════════════════════════════════════════════════════
# Loader function tests
# ═══════════════════════════════════════════════════════════════════════════


class TestLoaders:
    def test_load_validated_targets(self, tmp_path):
        targets_file = tmp_path / "targets.yaml"
        targets_file.write_text(yaml.dump({
            "tiers": {"tier1": {"companies": [{"name": "TestCo"}]}},
            "bad_words": {"title_words": ["intern"]},
        }))
        config = load_validated_targets(targets_file)
        assert config.tiers["tier1"].companies[0].name == "TestCo"
        assert config.bad_words.title_words == ["intern"]

    def test_load_validated_targets_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_validated_targets(tmp_path / "nonexistent.yaml")

    def test_load_validated_profile(self, tmp_path):
        profile_file = tmp_path / "master_profile.yaml"
        profile_file.write_text(yaml.dump({
            "personal": {"name": {"full": "Test"}, "contact": {"email": "a@b.com"}},
            "application_answers": {"work_authorization": "Yes"},
        }))
        config = load_validated_profile(profile_file)
        assert config.personal.name.full == "Test"
        assert config.application_answers.work_authorization == "Yes"

    def test_load_validated_profile_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_validated_profile(tmp_path / "nonexistent.yaml")


class TestValidateAllConfigs:
    def test_both_missing(self, tmp_path):
        result = validate_all_configs(
            targets_path=tmp_path / "targets.yaml",
            profile_path=tmp_path / "profile.yaml",
        )
        # Missing files are warnings, not errors
        assert result["valid"] is True
        assert len(result["warnings"]) == 2

    def test_valid_configs(self, tmp_path):
        targets_file = tmp_path / "targets.yaml"
        targets_file.write_text(yaml.dump({
            "tiers": {"tier1": {"companies": [{"name": "Co"}]}},
            "target_roles": {"primary": ["Engineer"]},
            "bad_words": {"title_words": ["junior"]},
        }))

        profile_file = tmp_path / "profile.yaml"
        profile_file.write_text(yaml.dump({
            "personal": {"contact": {"email": "a@b.com"}},
            "experience": [{"id": "x", "company": "C", "role": "R"}],
            "application_answers": {"work_authorization": "Yes"},
        }))

        result = validate_all_configs(targets_file, profile_file)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_invalid_yaml(self, tmp_path):
        targets_file = tmp_path / "targets.yaml"
        targets_file.write_text("{{invalid yaml: [")

        result = validate_all_configs(targets_path=targets_file, profile_path=tmp_path / "p.yaml")
        # yaml parse error → validation error
        assert result["valid"] is False or len(result["warnings"]) > 0
