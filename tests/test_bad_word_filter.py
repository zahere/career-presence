"""Tests for bad word filtering and experience range matching."""

import pytest

from scripts.discovery.job_searcher import _extract_experience_years, apply_targets_filter

# ═══════════════════════════════════════════════════════════════════════════
# Experience year extraction
# ═══════════════════════════════════════════════════════════════════════════


class TestExtractExperienceYears:
    def test_plus_years(self):
        assert _extract_experience_years("5+ years of experience") == 5

    def test_years_experience(self):
        assert _extract_experience_years("3 years experience in Python") == 3

    def test_range_years(self):
        assert _extract_experience_years("3-5 years of experience") == 3

    def test_minimum_years(self):
        assert _extract_experience_years("minimum 7 years") == 7

    def test_at_least(self):
        assert _extract_experience_years("at least 4 years of experience") == 4

    def test_professional_experience(self):
        assert _extract_experience_years("10 years of professional experience") == 10

    def test_yrs_abbreviation(self):
        assert _extract_experience_years("5+ yrs experience") == 5

    def test_no_match(self):
        assert _extract_experience_years("Great job opportunity") is None

    def test_empty_string(self):
        assert _extract_experience_years("") is None

    def test_none_input(self):
        assert _extract_experience_years(None) is None


# ═══════════════════════════════════════════════════════════════════════════
# Bad word filtering
# ═══════════════════════════════════════════════════════════════════════════


class TestBadWordFiltering:
    @pytest.fixture
    def targets_with_bad_words(self):
        return {
            "bad_words": {
                "title_words": ["junior", "director", "intern"],
                "description_words": ["security clearance required", "us citizen only"],
                "penalty_per_match": 5.0,
            },
            "experience_range": {
                "min_years": 3,
                "max_years": 15,
            },
        }

    def test_no_bad_words_no_penalty(self, targets_with_bad_words):
        jobs = [
            {
                "company": "TestCo",
                "title": "Senior AI Engineer",
                "description": "5+ years experience",
            }
        ]
        result = apply_targets_filter(jobs, targets_with_bad_words)
        assert result[0]["bad_word_penalty"] == 0.0
        assert result[0]["bad_words_matched"] == []

    def test_title_bad_word_penalty(self, targets_with_bad_words):
        jobs = [
            {"company": "TestCo", "title": "Junior AI Engineer", "description": "Some description"}
        ]
        result = apply_targets_filter(jobs, targets_with_bad_words)
        assert result[0]["bad_word_penalty"] == 5.0
        assert "title:junior" in result[0]["bad_words_matched"]

    def test_description_bad_word_penalty(self, targets_with_bad_words):
        jobs = [
            {
                "company": "TestCo",
                "title": "AI Engineer",
                "description": "security clearance required for this role",
            }
        ]
        result = apply_targets_filter(jobs, targets_with_bad_words)
        assert result[0]["bad_word_penalty"] == 5.0
        assert "desc:security clearance required" in result[0]["bad_words_matched"]

    def test_multiple_bad_words_stack(self, targets_with_bad_words):
        jobs = [
            {
                "company": "TestCo",
                "title": "Junior Intern Engineer",
                "description": "us citizen only",
            }
        ]
        result = apply_targets_filter(jobs, targets_with_bad_words)
        # "junior" + "intern" in title + "us citizen only" in description = 3 * 5.0 = 15.0
        assert result[0]["bad_word_penalty"] == 15.0
        assert len(result[0]["bad_words_matched"]) == 3

    def test_bad_words_case_insensitive(self, targets_with_bad_words):
        jobs = [{"company": "TestCo", "title": "JUNIOR AI Engineer", "description": "test"}]
        result = apply_targets_filter(jobs, targets_with_bad_words)
        assert result[0]["bad_word_penalty"] == 5.0

    def test_jobs_sorted_by_penalty(self, targets_with_bad_words):
        jobs = [
            {"company": "A", "title": "Junior Engineer", "description": "test"},
            {"company": "B", "title": "Senior Engineer", "description": "5+ years experience"},
        ]
        result = apply_targets_filter(jobs, targets_with_bad_words)
        # B (no penalty) should come before A (penalty)
        assert result[0]["company"] == "B"
        assert result[1]["company"] == "A"

    def test_soft_filter_keeps_all_jobs(self, targets_with_bad_words):
        """Bad words are soft penalties, not hard exclusions."""
        jobs = [
            {
                "company": "A",
                "title": "Junior Intern Director",
                "description": "security clearance required, us citizen only",
            },
        ]
        result = apply_targets_filter(jobs, targets_with_bad_words)
        # Job should still be in results (soft filter)
        assert len(result) == 1


# ═══════════════════════════════════════════════════════════════════════════
# Experience range matching
# ═══════════════════════════════════════════════════════════════════════════


class TestExperienceRangeMatching:
    @pytest.fixture
    def targets_with_exp_range(self):
        return {
            "experience_range": {
                "min_years": 3,
                "max_years": 15,
            },
            "bad_words": {
                "penalty_per_match": 5.0,
            },
        }

    def test_in_range(self, targets_with_exp_range):
        jobs = [
            {"company": "Co", "title": "Engineer", "description": "5+ years of experience required"}
        ]
        result = apply_targets_filter(jobs, targets_with_exp_range)
        assert result[0]["experience_match"] == "in_range"
        assert result[0]["required_experience_years"] == 5

    def test_under_qualified(self, targets_with_exp_range):
        jobs = [{"company": "Co", "title": "Engineer", "description": "1 year of experience"}]
        result = apply_targets_filter(jobs, targets_with_exp_range)
        assert result[0]["experience_match"] == "under_qualified"

    def test_over_qualified(self, targets_with_exp_range):
        jobs = [{"company": "Co", "title": "Engineer", "description": "20+ years of experience"}]
        result = apply_targets_filter(jobs, targets_with_exp_range)
        assert result[0]["experience_match"] == "over_qualified"

    def test_unknown_experience(self, targets_with_exp_range):
        jobs = [{"company": "Co", "title": "Engineer", "description": "Great opportunity"}]
        result = apply_targets_filter(jobs, targets_with_exp_range)
        assert result[0]["experience_match"] == "unknown"

    def test_experience_out_of_range_adds_penalty(self, targets_with_exp_range):
        jobs = [{"company": "Co", "title": "Engineer", "description": "1 year of experience"}]
        result = apply_targets_filter(jobs, targets_with_exp_range)
        assert result[0]["bad_word_penalty"] == 5.0  # One penalty for out of range

    def test_experience_in_range_no_extra_penalty(self, targets_with_exp_range):
        jobs = [{"company": "Co", "title": "Engineer", "description": "5+ years experience"}]
        result = apply_targets_filter(jobs, targets_with_exp_range)
        assert result[0]["bad_word_penalty"] == 0.0


class TestExclusionsStillWork:
    """Ensure hard exclusions from original behavior still work."""

    def test_excluded_company_removed(self):
        targets = {
            "exclusions": {"companies": ["BadCorp"], "keywords": []},
        }
        jobs = [{"company": "BadCorp", "title": "Engineer", "description": "test"}]
        result = apply_targets_filter(jobs, targets)
        assert len(result) == 0

    def test_excluded_keyword_removed(self):
        targets = {
            "exclusions": {"companies": [], "keywords": ["unpaid"]},
        }
        jobs = [{"company": "Co", "title": "Unpaid Intern", "description": "test"}]
        result = apply_targets_filter(jobs, targets)
        assert len(result) == 0

    def test_non_excluded_kept(self):
        targets = {
            "exclusions": {"companies": ["BadCorp"], "keywords": ["unpaid"]},
        }
        jobs = [{"company": "GoodCo", "title": "Engineer", "description": "paid role"}]
        result = apply_targets_filter(jobs, targets)
        assert len(result) == 1
