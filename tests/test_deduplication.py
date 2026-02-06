"""Tests for applied jobs deduplication."""

from datetime import datetime

import pytest

from scripts.tracking.tracker import Application, ApplicationTracker


@pytest.fixture
def tracker(tmp_path):
    """Create a tracker with a temporary database."""
    db_path = tmp_path / "test_applications.db"
    return ApplicationTracker(db_path=str(db_path))


@pytest.fixture
def sample_application():
    """Create a sample application."""
    now = datetime.now().isoformat()
    return Application(
        id="app_test_001",
        company="Anthropic",
        role="AI Engineer",
        job_url="https://boards.greenhouse.io/anthropic/jobs/12345",
        platform="greenhouse",
        status="applied",
        match_score=85.0,
        resume_variant=None,
        cover_letter=None,
        salary_range=None,
        location="Remote",
        remote_policy="remote",
        applied_at=now,
        response_at=None,
        keywords_matched=["python", "llm"],
        notes="Test application",
        created_at=now,
        updated_at=now,
    )


# ═══════════════════════════════════════════════════════════════════════════
# is_already_applied tests
# ═══════════════════════════════════════════════════════════════════════════


class TestIsAlreadyApplied:
    def test_not_applied(self, tracker):
        """No match returns None."""
        result = tracker.is_already_applied("Anthropic", "AI Engineer")
        assert result is None

    def test_match_by_url(self, tracker, sample_application):
        tracker.add_application(sample_application)
        result = tracker.is_already_applied(
            "Anthropic", "AI Engineer", job_url="https://boards.greenhouse.io/anthropic/jobs/12345"
        )
        assert result is not None
        assert result["id"] == "app_test_001"

    def test_match_by_company_role(self, tracker, sample_application):
        tracker.add_application(sample_application)
        result = tracker.is_already_applied("Anthropic", "AI Engineer")
        assert result is not None
        assert result["id"] == "app_test_001"

    def test_match_case_insensitive(self, tracker, sample_application):
        tracker.add_application(sample_application)
        result = tracker.is_already_applied("anthropic", "ai engineer")
        assert result is not None

    def test_ignores_discovered_status(self, tracker):
        """Jobs only in 'discovered' status should not count as applied."""
        now = datetime.now().isoformat()
        app = Application(
            id="app_disc_001",
            company="OpenAI",
            role="ML Engineer",
            job_url="https://openai.com/jobs/123",
            platform="direct",
            status="discovered",
            match_score=70.0,
            resume_variant=None,
            cover_letter=None,
            salary_range=None,
            location="Remote",
            remote_policy="remote",
            applied_at=None,
            response_at=None,
            keywords_matched=[],
            notes="",
            created_at=now,
            updated_at=now,
        )
        tracker.add_application(app)
        result = tracker.is_already_applied("OpenAI", "ML Engineer")
        assert result is None  # discovered doesn't count

    def test_applied_status_matches(self, tracker, sample_application):
        """Applied status should count as already applied."""
        tracker.add_application(sample_application)
        result = tracker.is_already_applied("Anthropic", "AI Engineer")
        assert result is not None
        assert result["status"] == "applied"

    def test_interviewing_status_matches(self, tracker, sample_application):
        tracker.add_application(sample_application)
        tracker.update_status("app_test_001", "responded")
        tracker.update_status("app_test_001", "interviewing")
        result = tracker.is_already_applied("Anthropic", "AI Engineer")
        assert result is not None
        assert result["status"] == "interviewing"

    def test_url_takes_priority(self, tracker, sample_application):
        """URL match should be found even with different company/role."""
        tracker.add_application(sample_application)
        result = tracker.is_already_applied(
            "Different Company",
            "Different Role",
            job_url="https://boards.greenhouse.io/anthropic/jobs/12345",
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════
# filter_already_applied tests
# ═══════════════════════════════════════════════════════════════════════════


class TestFilterAlreadyApplied:
    def test_empty_list(self, tracker):
        new, applied = tracker.filter_already_applied([])
        assert new == []
        assert applied == []

    def test_no_matches(self, tracker):
        jobs = [
            {"company": "TestCo", "title": "Engineer", "job_url": "http://example.com/1"},
        ]
        new, applied = tracker.filter_already_applied(jobs)
        assert len(new) == 1
        assert len(applied) == 0

    def test_filters_applied_jobs(self, tracker, sample_application):
        tracker.add_application(sample_application)

        jobs = [
            {
                "company": "Anthropic",
                "title": "AI Engineer",
                "job_url": "https://boards.greenhouse.io/anthropic/jobs/12345",
            },
            {"company": "OpenAI", "title": "ML Engineer", "job_url": "http://openai.com/jobs/1"},
        ]

        new, applied = tracker.filter_already_applied(jobs)
        assert len(new) == 1
        assert new[0]["company"] == "OpenAI"
        assert len(applied) == 1
        assert applied[0]["company"] == "Anthropic"
        assert applied[0]["already_applied"] is True
        assert applied[0]["existing_application_id"] == "app_test_001"

    def test_uses_title_or_role_key(self, tracker, sample_application):
        """Should work with both 'title' and 'role' keys."""
        tracker.add_application(sample_application)

        # Test with 'role' key instead of 'title'
        jobs = [{"company": "Anthropic", "role": "AI Engineer"}]
        new, applied = tracker.filter_already_applied(jobs)
        assert len(applied) == 1

    def test_multiple_applied_jobs(self, tracker):
        now = datetime.now().isoformat()
        for i, (company, role) in enumerate([("A", "R1"), ("B", "R2"), ("C", "R3")]):
            app = Application(
                id=f"app_{i}",
                company=company,
                role=role,
                job_url=f"http://example.com/{i}",
                platform="direct",
                status="applied",
                match_score=80.0,
                resume_variant=None,
                cover_letter=None,
                salary_range=None,
                location="Remote",
                remote_policy="remote",
                applied_at=now,
                response_at=None,
                keywords_matched=[],
                notes="",
                created_at=now,
                updated_at=now,
            )
            tracker.add_application(app)

        jobs = [
            {"company": "A", "title": "R1"},
            {"company": "B", "title": "R2"},
            {"company": "D", "title": "R4"},  # new
        ]

        new, applied = tracker.filter_already_applied(jobs)
        assert len(new) == 1
        assert len(applied) == 2
        assert new[0]["company"] == "D"
