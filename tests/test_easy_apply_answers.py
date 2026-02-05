"""Tests for LinkedIn Easy Apply answer resolver."""

import pytest
import yaml
from pathlib import Path

from scripts.submission.easy_apply_answers import AnswerResolver, ResolvedAnswer


@pytest.fixture
def resolver():
    """Create a resolver with test answers."""
    return AnswerResolver(
        answers={
            "work_authorization": "Yes",
            "visa_sponsorship": "No",
            "years_of_experience": "5",
            "education_level": "Bachelor's Degree",
            "salary_expectation": "150000",
            "start_date": "Immediately",
            "willing_to_relocate": "Yes",
        },
        custom_answers={
            "How did you hear about us?": "LinkedIn",
            "Are you comfortable working remotely?": "Yes",
        },
    )


@pytest.fixture
def resolver_from_file(tmp_path):
    """Create a resolver from a test profile file."""
    profile = {
        "application_answers": {
            "work_authorization": "Yes",
            "visa_sponsorship": "No",
            "years_of_experience": "5",
            "custom_answers": {
                "How did you hear about us?": "LinkedIn",
            },
        }
    }
    path = tmp_path / "profile.yaml"
    path.write_text(yaml.dump(profile))
    return AnswerResolver.from_profile(path)


# ═══════════════════════════════════════════════════════════════════════════
# Pattern matching tests
# ═══════════════════════════════════════════════════════════════════════════


class TestPatternMatching:
    def test_work_authorization(self, resolver):
        result = resolver.resolve("Are you authorized to work in the US?")
        assert result is not None
        assert result.answer == "Yes"
        assert "work_authorization" in result.source

    def test_work_authorization_variant(self, resolver):
        result = resolver.resolve("Do you have the legal right to work in this country?")
        assert result is not None
        assert result.answer == "Yes"

    def test_visa_sponsorship(self, resolver):
        result = resolver.resolve("Do you require visa sponsorship?")
        assert result is not None
        assert result.answer == "No"
        assert "visa_sponsorship" in result.source

    def test_visa_sponsorship_variant(self, resolver):
        result = resolver.resolve("Will you need immigration sponsorship now or in the future?")
        assert result is not None
        assert result.answer == "No"

    def test_years_of_experience(self, resolver):
        result = resolver.resolve("How many years of experience do you have?")
        assert result is not None
        assert result.answer == "5"

    def test_years_experience_variant(self, resolver):
        result = resolver.resolve("Total years of relevant experience in this field?")
        assert result is not None
        assert result.answer == "5"

    def test_education_level(self, resolver):
        result = resolver.resolve("What is your highest degree?")
        assert result is not None
        assert result.answer == "Bachelor's Degree"

    def test_salary_expectation(self, resolver):
        result = resolver.resolve("What is your desired salary?")
        assert result is not None
        assert result.answer == "150000"

    def test_start_date(self, resolver):
        result = resolver.resolve("When can you start?")
        assert result is not None
        assert result.answer == "Immediately"

    def test_start_date_notice(self, resolver):
        result = resolver.resolve("What is your notice period?")
        assert result is not None
        assert result.answer == "Immediately"

    def test_willing_to_relocate(self, resolver):
        result = resolver.resolve("Are you willing to relocate?")
        assert result is not None
        assert result.answer == "Yes"

    def test_no_match(self, resolver):
        result = resolver.resolve("What is your favorite color?")
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# Custom answers tests
# ═══════════════════════════════════════════════════════════════════════════


class TestCustomAnswers:
    def test_exact_custom_match(self, resolver):
        result = resolver.resolve("How did you hear about us?")
        assert result is not None
        assert result.answer == "LinkedIn"
        assert result.source == "custom_answers"
        assert result.confidence == 0.95

    def test_substring_custom_match(self, resolver):
        result = resolver.resolve("How did you hear about us? (required)")
        assert result is not None
        assert result.answer == "LinkedIn"

    def test_custom_takes_priority(self, resolver):
        """Custom answers should be checked before pattern matching."""
        # Add a custom answer that could also match a pattern
        resolver.custom_answers["Do you require visa sponsorship?"] = "Custom No"
        result = resolver.resolve("Do you require visa sponsorship?")
        assert result is not None
        assert result.answer == "Custom No"
        assert result.source == "custom_answers"


# ═══════════════════════════════════════════════════════════════════════════
# Dropdown option fitting tests
# ═══════════════════════════════════════════════════════════════════════════


class TestFitToOptions:
    def test_exact_match(self, resolver):
        result = resolver.resolve(
            "Are you authorized to work?",
            field_type="dropdown",
            options=["Yes", "No"],
        )
        assert result is not None
        assert result.answer == "Yes"

    def test_case_insensitive_match(self, resolver):
        result = resolver.resolve(
            "Are you authorized to work?",
            field_type="dropdown",
            options=["YES", "NO"],
        )
        assert result is not None
        assert result.answer == "YES"

    def test_substring_match(self, resolver):
        result = resolver.resolve(
            "What is your highest degree?",
            field_type="dropdown",
            options=["High School", "Associate's Degree", "Bachelor's Degree", "Master's Degree", "PhD"],
        )
        assert result is not None
        assert result.answer == "Bachelor's Degree"

    def test_yes_no_normalization(self):
        resolver = AnswerResolver(answers={"work_authorization": "true"})
        result = resolver.resolve(
            "Are you authorized to work?",
            options=["Yes", "No"],
        )
        assert result is not None
        assert result.answer == "Yes"

    def test_no_matching_option_returns_original(self, resolver):
        result = resolver.resolve(
            "How many years of experience?",
            options=["0-2", "3-5", "6-10", "10+"],
        )
        assert result is not None
        # "5" is a substring of "3-5", so substring matching picks that option
        assert result.answer == "3-5"

    def test_truly_no_matching_option(self, resolver):
        result = resolver.resolve(
            "How many years of experience?",
            options=["None", "Some", "Lots"],
        )
        assert result is not None
        # No option contains "5" as substring, returns original answer
        assert result.answer == "5"


# ═══════════════════════════════════════════════════════════════════════════
# Batch resolution tests
# ═══════════════════════════════════════════════════════════════════════════


class TestResolveAll:
    def test_batch_resolve(self, resolver):
        questions = [
            {"question": "Are you authorized to work?", "field_type": "dropdown"},
            {"question": "How many years of experience?", "field_type": "text"},
            {"question": "What is your favorite color?", "field_type": "text"},  # No match
        ]
        results = resolver.resolve_all(questions)
        assert len(results) == 2  # third has no match

    def test_batch_with_options(self, resolver):
        questions = [
            {
                "question": "Are you authorized to work in the US?",
                "field_type": "dropdown",
                "options": ["Yes", "No"],
            },
        ]
        results = resolver.resolve_all(questions)
        assert len(results) == 1
        assert results[0].answer == "Yes"

    def test_empty_batch(self, resolver):
        assert resolver.resolve_all([]) == []


# ═══════════════════════════════════════════════════════════════════════════
# File loading tests
# ═══════════════════════════════════════════════════════════════════════════


class TestFromProfile:
    def test_loads_from_file(self, resolver_from_file):
        result = resolver_from_file.resolve("Are you authorized to work?")
        assert result is not None
        assert result.answer == "Yes"

    def test_loads_custom_answers(self, resolver_from_file):
        result = resolver_from_file.resolve("How did you hear about us?")
        assert result is not None
        assert result.answer == "LinkedIn"

    def test_missing_file_returns_empty(self, tmp_path):
        resolver = AnswerResolver.from_profile(tmp_path / "nonexistent.yaml")
        assert resolver.answers == {}
        assert resolver.custom_answers == {}

    def test_empty_profile(self, tmp_path):
        path = tmp_path / "empty.yaml"
        path.write_text("{}")
        resolver = AnswerResolver.from_profile(path)
        assert resolver.answers == {}


class TestResolvedAnswer:
    def test_dataclass(self):
        answer = ResolvedAnswer(
            question="test?",
            answer="yes",
            confidence=0.9,
            source="test",
            field_type="text",
        )
        assert answer.question == "test?"
        assert answer.confidence == 0.9

    def test_empty_question(self, resolver):
        assert resolver.resolve("") is None
        assert resolver.resolve(None) is None
