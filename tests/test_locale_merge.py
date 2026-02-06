"""Tests for locale merge logic and locale-aware config loading."""

import copy

import pytest

from scripts.discovery.job_searcher import (
    _merge_locale,
    apply_targets_filter,
    load_targets,
)

# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def base_config():
    """Minimal base targets config (no locales key)."""
    return {
        "version": "1.0",
        "tiers": {
            "tier1": {
                "companies": [
                    {
                        "name": "Anthropic",
                        "careers_url": "https://anthropic.com/careers",
                        "priority": 1,
                    },
                ]
            },
            "tier2": {
                "companies": [
                    {
                        "name": "Databricks",
                        "careers_url": "https://databricks.com/careers",
                        "priority": 2,
                    },
                ]
            },
        },
        "search_params": {
            "locations": {
                "preferred": ["Remote"],
                "acceptable": ["San Francisco, CA"],
            },
            "salary": {"minimum_usd": 150000, "currency": "USD"},
        },
        "bad_words": {
            "title_words": ["junior", "intern"],
            "description_words": ["security clearance required"],
            "penalty_per_match": 5.0,
        },
        "experience_range": {"min_years": 3, "max_years": 15},
        "target_roles": {
            "primary": ["AI Engineer"],
            "secondary": ["Platform Engineer"],
        },
    }


@pytest.fixture
def israel_overrides():
    """Israel locale overrides."""
    return {
        "search_params": {
            "locations": {
                "preferred": ["Tel Aviv, Israel", "Herzliya, Israel"],
                "acceptable": ["Haifa, Israel", "Remote"],
            },
            "country": "Israel",
            "salary": {"minimum_ils": 45000, "currency": "ILS"},
        },
        "tiers": {
            "tier1": {
                "companies": [
                    {
                        "name": "monday.com",
                        "careers_url": "https://monday.com/careers",
                        "priority": 1,
                    },
                ]
            },
            "tier2": {
                "companies": [
                    {
                        "name": "Tabnine",
                        "careers_url": "https://tabnine.com/careers",
                        "priority": 2,
                    },
                ]
            },
        },
        "bad_words": {
            "description_words": ["dod clearance", "must be eligible for us security clearance"],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# _merge_locale unit tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMergeLocale:
    def test_tiers_extended(self, base_config, israel_overrides):
        merged = _merge_locale(base_config, israel_overrides)
        tier1_names = [c["name"] for c in merged["tiers"]["tier1"]["companies"]]
        assert "Anthropic" in tier1_names
        assert "monday.com" in tier1_names

    def test_tier2_extended(self, base_config, israel_overrides):
        merged = _merge_locale(base_config, israel_overrides)
        tier2_names = [c["name"] for c in merged["tiers"]["tier2"]["companies"]]
        assert "Databricks" in tier2_names
        assert "Tabnine" in tier2_names

    def test_locations_replaced(self, base_config, israel_overrides):
        merged = _merge_locale(base_config, israel_overrides)
        locs = merged["search_params"]["locations"]
        assert "Tel Aviv, Israel" in locs["preferred"]
        assert "Remote" not in locs["preferred"]
        assert "San Francisco, CA" not in locs.get("acceptable", [])

    def test_country_replaced(self, base_config, israel_overrides):
        merged = _merge_locale(base_config, israel_overrides)
        assert merged["search_params"]["country"] == "Israel"

    def test_salary_replaced(self, base_config, israel_overrides):
        merged = _merge_locale(base_config, israel_overrides)
        salary = merged["search_params"]["salary"]
        assert salary["currency"] == "ILS"
        assert salary["minimum_ils"] == 45000
        assert "minimum_usd" not in salary

    def test_bad_words_extended_and_deduped(self, base_config, israel_overrides):
        merged = _merge_locale(base_config, israel_overrides)
        desc_words = merged["bad_words"]["description_words"]
        assert "security clearance required" in desc_words
        assert "dod clearance" in desc_words
        assert "must be eligible for us security clearance" in desc_words
        # No duplicates
        assert len(desc_words) == len({w.lower() for w in desc_words})

    def test_bad_words_title_words_inherited(self, base_config, israel_overrides):
        """Locale doesn't override title_words, so base title_words persist."""
        merged = _merge_locale(base_config, israel_overrides)
        assert "junior" in merged["bad_words"]["title_words"]
        assert "intern" in merged["bad_words"]["title_words"]

    def test_bad_words_dedup_case_insensitive(self, base_config):
        """Duplicate words (case-insensitive) are removed."""
        overrides = {
            "bad_words": {
                "description_words": ["Security Clearance Required"],
            },
        }
        merged = _merge_locale(base_config, overrides)
        desc_lower = [w.lower() for w in merged["bad_words"]["description_words"]]
        assert desc_lower.count("security clearance required") == 1

    def test_base_not_mutated(self, base_config, israel_overrides):
        original = copy.deepcopy(base_config)
        _merge_locale(base_config, israel_overrides)
        assert base_config == original

    def test_empty_override(self, base_config):
        merged = _merge_locale(base_config, {})
        assert merged == base_config

    def test_target_roles_inherited(self, base_config, israel_overrides):
        merged = _merge_locale(base_config, israel_overrides)
        assert merged["target_roles"] == base_config["target_roles"]

    def test_experience_range_inherited(self, base_config, israel_overrides):
        merged = _merge_locale(base_config, israel_overrides)
        assert merged["experience_range"] == base_config["experience_range"]

    def test_new_tier_from_locale(self, base_config):
        """Locale can add a tier that doesn't exist in base."""
        overrides = {
            "tiers": {
                "tier4": {
                    "companies": [
                        {"name": "NewCo", "priority": 4},
                    ]
                },
            },
        }
        merged = _merge_locale(base_config, overrides)
        assert "tier4" in merged["tiers"]
        assert merged["tiers"]["tier4"]["companies"][0]["name"] == "NewCo"
        # Existing tiers untouched
        assert len(merged["tiers"]["tier1"]["companies"]) == 1


# ═══════════════════════════════════════════════════════════════════════════
# load_targets with locale
# ═══════════════════════════════════════════════════════════════════════════


class TestLoadTargetsWithLocale:
    def test_without_locale(self):
        """Loading without locale returns base config (no locales key)."""
        targets = load_targets()
        assert "locales" not in targets
        assert "tiers" in targets

    def test_with_valid_locale(self):
        """Loading with 'israel' locale returns merged config."""
        targets = load_targets(locale="israel")
        # Should have Israel companies appended
        tier1_names = [c["name"] for c in targets["tiers"]["tier1"]["companies"]]
        assert "monday.com" in tier1_names
        # Base companies still present
        assert "Anthropic" in tier1_names
        # Locales key stripped
        assert "locales" not in targets

    def test_with_invalid_locale(self):
        """Loading with unknown locale raises ValueError."""
        with pytest.raises(ValueError, match="Unknown locale"):
            load_targets(locale="narnia")


# ═══════════════════════════════════════════════════════════════════════════
# Integration: locale config flows through apply_targets_filter
# ═══════════════════════════════════════════════════════════════════════════


class TestLocaleIntegration:
    def test_israel_companies_get_correct_tier(self):
        """Israel-locale companies should be tiered correctly."""
        targets = load_targets(locale="israel")
        jobs = [
            {"company": "monday.com", "title": "AI Engineer", "description": "5+ years experience"},
            {"company": "Tabnine", "title": "ML Engineer", "description": "3+ years experience"},
            {"company": "Snyk", "title": "Platform Engineer", "description": "4+ years experience"},
        ]
        result = apply_targets_filter(jobs, targets)
        tier_map = {j["company"]: j["target_tier"] for j in result}
        assert tier_map["monday.com"] == "tier1"
        assert tier_map["Tabnine"] == "tier2"
        assert tier_map["Snyk"] == "tier3"

    def test_israel_bad_words_create_penalties(self):
        """Israel-specific bad words should add penalties."""
        targets = load_targets(locale="israel")
        jobs = [
            {
                "company": "SomeCo",
                "title": "Engineer",
                "description": "requires dod clearance for this position",
            },
        ]
        result = apply_targets_filter(jobs, targets)
        assert result[0]["bad_word_penalty"] > 0
        assert any("dod clearance" in w for w in result[0]["bad_words_matched"])

    def test_base_bad_words_still_apply_with_locale(self):
        """Base bad words should still apply when using a locale."""
        targets = load_targets(locale="israel")
        jobs = [
            {
                "company": "SomeCo",
                "title": "Junior Engineer",
                "description": "great opportunity",
            },
        ]
        result = apply_targets_filter(jobs, targets)
        assert result[0]["bad_word_penalty"] > 0
        assert "title:junior" in result[0]["bad_words_matched"]
