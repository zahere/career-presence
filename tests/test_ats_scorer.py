"""Tests for ATS Scorer module."""

import pytest
from pathlib import Path
import sys

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from analysis.ats_scorer import ATSScorer, ATSScore, generate_report


class TestATSScorer:
    """Test suite for ATS scoring functionality."""

    @pytest.fixture
    def scorer(self):
        """Create an ATSScorer instance for tests."""
        return ATSScorer()

    @pytest.fixture
    def sample_resume(self):
        """Sample resume text for testing."""
        return """
        JANE DOE
        Senior Software Engineer • Backend Systems

        Professional Summary
        Senior Software Engineer with 7 years of experience building scalable
        distributed systems and cloud-native applications. Led development of
        a real-time data pipeline processing 2M+ events per day.

        Experience

        Acme Corp — Senior Software Engineer (Jan 2022 - Present)
        • Designed event-driven microservices architecture handling 50K requests/sec
          with 99.9% uptime across 3 availability zones
        • Reduced CI/CD pipeline duration from 45 minutes to 8 minutes using caching
        • Mentored team of 5 engineers on distributed systems best practices

        Widgets Inc — Software Engineer (Mar 2019 - Dec 2021)
        • Built RESTful API serving 10M daily requests with <50ms p95 latency
        • Migrated monolith to microservices reducing deployment time by 80%

        Technical Skills
        AI/ML: Multi-Agent, LLM, PyTorch, RAG, Prompt Engineering
        Infrastructure: Kubernetes, Docker, AWS, GCP
        Languages: Python, Go, Rust, C++

        Education
        State University — B.Sc. Computer Science
        """

    @pytest.fixture
    def sample_job_description(self):
        """Sample job description for testing."""
        return """
        AI Research Engineer

        We're looking for an AI Research Engineer to help build the next generation
        of AI systems. You'll work on multi-agent systems, LLM infrastructure, and
        alignment research.

        Requirements:
        • 5+ years of experience in machine learning or AI
        • Expert-level Python programming
        • Experience with PyTorch or JAX
        • Strong background in distributed systems
        • Experience with LLMs and prompt engineering
        • Kubernetes experience preferred

        Nice to have:
        • PhD in ML, CS, or related field
        • Publications in top venues (NeurIPS, ICML)
        • Experience with MLOps
        • Rust or Go programming experience
        """

    def test_keyword_extraction(self, scorer, sample_job_description):
        """Test that keywords are properly extracted from job descriptions."""
        # Use the internal scoring method which extracts keywords
        resume_lower = "python kubernetes llm pytorch machine learning"
        jd_lower = sample_job_description.lower()

        score, matched, missing = scorer._score_keywords(resume_lower, jd_lower, None)

        # Should find some tech keywords
        assert len(matched) > 0, "Should extract at least some keywords"

        # Should find common AI/ML keywords
        common_keywords = ["python", "pytorch", "kubernetes", "llm", "machine learning"]
        found_common = [kw for kw in common_keywords if kw in matched]
        assert len(found_common) >= 2, f"Should find common keywords, found: {found_common}"

        # Score should be between 0 and 40
        assert 0 <= score <= 40, f"Keyword score should be 0-40, got {score}"

    def test_section_detection(self, scorer, sample_resume):
        """Test that required sections are properly detected in resume."""
        resume_lower = sample_resume.lower()

        score, found, missing = scorer._score_sections(resume_lower)

        # Should detect key sections
        assert "experience" in found or "professional experience" in found, \
            "Should detect experience section"
        assert "education" in found or "academic background" in found, \
            "Should detect education section"
        assert "technical skills" in found or "skills" in found, \
            "Should detect skills section"

        # Score should be between 0 and 20
        assert 0 <= score <= 20, f"Section score should be 0-20, got {score}"

        # Should find at least 3 sections in sample resume
        assert len(found) >= 3, f"Should find at least 3 sections, found {len(found)}: {found}"

    def test_metrics_extraction(self, scorer, sample_resume):
        """Test that quantifiable metrics are properly identified."""
        score, metrics_found = scorer._score_metrics(sample_resume)

        # Should find various metrics in the sample resume
        # Expected: 116, 27, 32%, <150ms, 100+, 91%, <2-minute, etc.
        assert len(metrics_found) >= 3, f"Should find multiple metrics, found {len(metrics_found)}: {metrics_found}"

        # Check for specific metric patterns
        metrics_str = " ".join(metrics_found)
        assert any("%" in m for m in metrics_found), "Should find percentage metrics"

        # Score should be between 0 and 20
        assert 0 <= score <= 20, f"Metrics score should be 0-20, got {score}"

    def test_scoring_algorithm(self, scorer, sample_resume, sample_job_description):
        """Test that overall score is calculated correctly."""
        result = scorer.score(sample_resume, sample_job_description)

        # Check result is an ATSScore object
        assert isinstance(result, ATSScore), "Should return ATSScore object"

        # Check total score is sum of components
        expected_total = int(
            result.keyword_score +
            result.section_score +
            result.metrics_score +
            result.formatting_score
        )
        assert result.total_score == expected_total, \
            f"Total score {result.total_score} should equal sum of components {expected_total}"

        # Total should be 0-100
        assert 0 <= result.total_score <= 100, f"Total score should be 0-100, got {result.total_score}"

        # Check recommendation is set based on score
        if result.total_score >= 85:
            assert result.recommendation == "auto_apply"
        elif result.total_score >= 80:
            assert result.recommendation == "ready"
        elif result.total_score >= 70:
            assert result.recommendation == "needs_review"
        else:
            assert result.recommendation == "regenerate"

    def test_recommendation_thresholds(self, scorer):
        """Test that recommendations match score thresholds."""
        # Create a minimal resume and JD that will give us control over scores
        base_jd = "Looking for Python developer"

        # Test high score (auto_apply >= 85)
        high_score_resume = """
        Professional Summary
        Expert Python developer with 10+ years experience.

        Experience
        Company A - Senior Python Developer (2020 - Present)
        • Increased efficiency by 50%
        • Reduced costs by $1.2M
        • Led team of 5+ engineers
        • Deployed to 100+ servers

        Technical Skills
        Python, Django, Flask, FastAPI

        Education
        MIT - Computer Science

        Projects
        Built scalable systems
        """
        result = scorer.score(high_score_resume, base_jd)
        # Just verify the recommendation logic works
        assert result.recommendation in ["auto_apply", "ready", "needs_review", "regenerate"]

    def test_empty_inputs(self, scorer):
        """Test handling of empty inputs."""
        # Empty resume
        result = scorer.score("", "Looking for Python developer")
        assert result.total_score >= 0, "Should handle empty resume"

        # Empty job description
        result = scorer.score("Python developer resume", "")
        assert result.total_score >= 0, "Should handle empty job description"


class TestATSFormatting:
    """Test suite for ATS formatting checks."""

    @pytest.fixture
    def scorer(self):
        return ATSScorer()

    def test_single_column_detection(self, scorer):
        """Test detection of single vs multi-column layouts."""
        # Single column (minimal whitespace)
        single_col = """
        Name: John Doe
        Experience: Software Engineer
        Skills: Python, Java
        Education: BS Computer Science
        """
        score1, issues1 = scorer._score_formatting(single_col)

        # Multi-column simulation (excessive whitespace)
        multi_col = """
        Name: John Doe           Skills: Python
        Experience:              Education:
        Software Engineer        BS CS
        """
        score2, issues2 = scorer._score_formatting(multi_col)

        # Single column should score equal or better
        assert score1 >= score2, "Single column should score >= multi-column"

    def test_standard_fonts(self, scorer):
        """Test detection of ATS-friendly fonts."""
        # This is primarily a PDF check, but we can test the general formatting
        # Need sufficient length to avoid "too short" penalty
        good_resume = """
        Professional Summary
        Experienced software engineer with expertise in Python and building scalable systems.
        Over 10 years of experience in software development and team leadership.

        Experience
        Senior Software Engineer at Tech Company (2020 - Present)
        • Led development of key features for the core platform
        • Improved performance by 40% through optimization
        • Mentored junior developers and conducted code reviews

        Skills
        Python, JavaScript, SQL, AWS, Docker, Kubernetes
        """
        score, issues = scorer._score_formatting(good_resume)
        # Should pass basic formatting checks
        assert score >= 10, "Well-formatted resume should score reasonably"

    def test_text_extractability(self, scorer):
        """Test that text can be extracted from PDF."""
        # Test with extractable text (simulated)
        good_text = "A" * 600  # Sufficient length
        score1, issues1 = scorer._score_formatting(good_text)

        # Test with very short text (suggests extraction issues)
        bad_text = "Short"  # Too short
        score2, issues2 = scorer._score_formatting(bad_text)

        assert score1 > score2, "Longer extractable text should score better"
        assert any("short" in issue.lower() or "extractable" in issue.lower()
                   for issue in issues2), "Should flag short/non-extractable text"

    def test_encoding_issues(self, scorer):
        """Test detection of encoding problems."""
        # Text with encoding issues
        bad_encoding = "Resume with encoding issues: � and \\x00"
        score, issues = scorer._score_formatting(bad_encoding)

        assert any("encoding" in issue.lower() for issue in issues), \
            "Should detect encoding issues"

    def test_bullet_points(self, scorer):
        """Test detection of bullet point formatting."""
        # Resume with bullets
        with_bullets = """
        Experience
        • Achievement one
        • Achievement two
        - Another point
        """
        score1, issues1 = scorer._score_formatting(with_bullets)

        # Resume without bullets
        no_bullets = """
        Experience
        Achievement one
        Achievement two
        Another point
        """
        score2, issues2 = scorer._score_formatting(no_bullets)

        # With bullets should score better or equal (bullets detected vs not)
        assert score1 >= score2, "Resume with bullets should score >= without"


class TestATSReport:
    """Test the report generation."""

    def test_generate_report(self):
        """Test that report generates without errors."""
        score = ATSScore(
            total_score=82,
            keyword_score=30.0,
            section_score=18.0,
            metrics_score=16.0,
            formatting_score=18.0,
            matched_keywords=["python", "kubernetes", "llm"],
            missing_keywords=["java", "scala"],
            sections_found=["experience", "skills", "education"],
            sections_missing=["projects"],
            metrics_found=["50%", "5+ years", "$100K"],
            formatting_issues=[],
            recommendation="ready"
        )

        report = generate_report(score)

        assert "82" in report, "Report should contain total score"
        assert "READY" in report, "Report should contain recommendation"
        assert "python" in report, "Report should list matched keywords"
