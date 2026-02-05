"""
LinkedIn Easy Apply Question Answering

Maps common application questions to answers from master_profile.yaml.
Uses pattern matching for standard questions and fuzzy matching for
dropdown option selection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"

# Standard question patterns mapped to answer keys in application_answers
QUESTION_PATTERNS: dict[str, list[str]] = {
    "work_authorization": [
        r"(?:are you|do you have).*(?:authorized|legally|permitted).*(?:work|employment)",
        r"work\s*(?:authorization|authorisation|permit)",
        r"(?:legally|authorized)\s*(?:to\s*)?work",
        r"right\s*to\s*work",
        r"eligible\s*to\s*work",
    ],
    "visa_sponsorship": [
        r"(?:require|need).*(?:visa|sponsorship)",
        r"visa\s*(?:sponsorship|support|status)",
        r"(?:immigration|work)\s*(?:sponsorship|visa)",
        r"sponsor.*(?:visa|work\s*permit)",
    ],
    "years_of_experience": [
        r"(?:how\s*many|number\s*of)?\s*years?\s*(?:of\s*)?(?:\w+\s+)?(?:experience|exp)",
        r"total\s*(?:years?|yrs?)\s*(?:of\s*)?(?:\w+\s+)?(?:experience|exp)",
        r"(?:professional|relevant|work)\s*experience\s*(?:in\s*)?(?:years?|yrs?)",
    ],
    "education_level": [
        r"(?:highest|education)\s*(?:level|degree|qualification)",
        r"(?:degree|education)\s*(?:obtained|completed|level)",
        r"what\s*(?:is\s*)?(?:your\s*)?(?:highest\s*)?(?:degree|education)",
    ],
    "salary_expectation": [
        r"(?:salary|compensation|pay)\s*(?:expectation|requirement|range|desired)",
        r"(?:expected|desired|minimum)\s*(?:salary|compensation|pay)",
        r"(?:what|how\s*much).*(?:salary|compensation|pay)",
    ],
    "start_date": [
        r"(?:when|how\s*soon).*(?:start|available|begin|join)",
        r"(?:start|availability|available)\s*(?:date|when)",
        r"(?:earliest|soonest)\s*(?:start|join|available)",
        r"notice\s*period",
    ],
    "willing_to_relocate": [
        r"(?:willing|open|able)\s*(?:to\s*)?relocat",
        r"relocation",
        r"(?:willing|open)\s*(?:to\s*)?move",
    ],
}


@dataclass
class ResolvedAnswer:
    """A resolved answer for an application question."""

    question: str
    answer: str
    confidence: float  # 0.0 - 1.0
    source: str  # e.g. "application_answers.work_authorization", "custom_answers"
    field_type: str = "text"  # text, dropdown, radio, checkbox


@dataclass
class AnswerResolver:
    """
    Resolves application questions to answers using the master profile.

    Loads application_answers from master_profile.yaml and matches questions
    using regex patterns and fuzzy matching.
    """

    answers: dict[str, str] = field(default_factory=dict)
    custom_answers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_profile(cls, profile_path: Path | None = None) -> AnswerResolver:
        """Load answer resolver from master_profile.yaml."""
        path = profile_path or CONFIG_DIR / "master_profile.yaml"
        if not path.exists():
            return cls()

        with open(path) as f:
            profile = yaml.safe_load(f) or {}

        app_answers = profile.get("application_answers", {})
        custom = app_answers.pop("custom_answers", {}) if isinstance(app_answers, dict) else {}

        return cls(
            answers={k: str(v) for k, v in app_answers.items() if v},
            custom_answers={k: str(v) for k, v in custom.items() if v},
        )

    def resolve(
        self,
        question: str,
        field_type: str = "text",
        options: list[str] | None = None,
    ) -> ResolvedAnswer | None:
        """
        Resolve a single question to an answer.

        Args:
            question: The question text
            field_type: The form field type (text, dropdown, radio, checkbox)
            options: Available options for dropdown/radio fields

        Returns:
            ResolvedAnswer if a match is found, None otherwise.
        """
        if not question:
            return None

        question_lower = question.lower().strip()

        # 1. Check custom_answers first (exact/substring match)
        for custom_q, custom_a in self.custom_answers.items():
            if custom_q.lower() in question_lower or question_lower in custom_q.lower():
                answer = self._fit_to_options(custom_a, options) if options else custom_a
                return ResolvedAnswer(
                    question=question,
                    answer=answer,
                    confidence=0.95,
                    source="custom_answers",
                    field_type=field_type,
                )

        # 2. Pattern match against known question types
        for answer_key, patterns in QUESTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    raw_answer = self.answers.get(answer_key)
                    if raw_answer:
                        answer = (
                            self._fit_to_options(raw_answer, options) if options else raw_answer
                        )
                        return ResolvedAnswer(
                            question=question,
                            answer=answer,
                            confidence=0.85,
                            source=f"application_answers.{answer_key}",
                            field_type=field_type,
                        )
                    break  # Pattern matched but no answer configured

        return None

    def resolve_all(self, questions: list[dict[str, str]]) -> list[ResolvedAnswer]:
        """
        Batch-resolve a list of questions.

        Args:
            questions: List of dicts with keys: "question", "field_type", "options" (optional)

        Returns:
            List of ResolvedAnswer for questions that could be resolved.
        """
        results = []
        for q in questions:
            options_raw = q.get("options")
            options = options_raw if isinstance(options_raw, list) else None
            resolved = self.resolve(
                question=q.get("question", ""),
                field_type=q.get("field_type", "text"),
                options=options,
            )
            if resolved:
                results.append(resolved)
        return results

    @staticmethod
    def _fit_to_options(answer: str, options: list[str] | None) -> str:
        """
        Find the best matching option from a dropdown/radio list.

        Uses case-insensitive substring matching, then falls back to
        the original answer if no match is found.
        """
        if not options:
            return answer

        answer_lower = answer.lower().strip()

        # Exact match (case-insensitive)
        for opt in options:
            if opt.lower().strip() == answer_lower:
                return opt

        # Substring match: answer contained in option or vice versa
        for opt in options:
            opt_lower = opt.lower().strip()
            if answer_lower in opt_lower or opt_lower in answer_lower:
                return opt

        # Yes/No normalization
        if answer_lower in ("yes", "true", "1"):
            for opt in options:
                if opt.lower().strip() in ("yes", "true", "1"):
                    return opt
        if answer_lower in ("no", "false", "0"):
            for opt in options:
                if opt.lower().strip() in ("no", "false", "0"):
                    return opt

        # No match found — return original answer
        return answer
