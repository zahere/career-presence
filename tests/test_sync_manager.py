"""Tests for the Platform Sync Manager."""

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.sync.sync_manager import PlatformSyncManager


@pytest.fixture()
def minimal_profile(tmp_path: Path) -> dict:
    """Create a minimal master_profile.yaml and return its data."""
    profile = {
        "personal": {
            "name": {"full": "Test User", "first": "Test", "last": "User"},
            "tagline": "Test Role",
            "headlines": {
                "resume": "Test Role • Specialty",
                "linkedin": "Building Project | Test Role",
                "github": "Test Role | Building Things",
                "website": "Test Role & Creator",
            },
            "contact": {
                "email": "test@example.com",
                "phone": "+1-555-0000",
                "location": "Remote",
                "timezone": "UTC",
            },
            "social": {
                "linkedin": "https://linkedin.com/in/testuser",
                "github": "https://github.com/testuser",
                "twitter": "",
                "website": "",
            },
            "languages": [{"language": "English", "proficiency": "Native"}],
        },
        "summaries": {
            "resume": "Test resume summary.",
            "linkedin": "Test linkedin summary.",
            "github": "## Hi\nTest github summary.",
            "website": "Test website summary.",
        },
        "experience": [
            {
                "id": "job1",
                "company": "Acme Corp",
                "role": "Senior Engineer",
                "type": "employee",
                "location": "Remote",
                "start_date": "2023-01",
                "end_date": None,
                "short_description": "Building things.",
                "bullets": [
                    {
                        "text": "Achieved 50% improvement in performance",
                        "metrics": ["50%"],
                        "keywords": ["performance"],
                    },
                    {
                        "text": "Led team of 5 engineers",
                        "metrics": ["5 engineers"],
                        "keywords": ["leadership"],
                    },
                ],
                "technologies": ["Python", "Go"],
            },
            {
                "id": "job2",
                "company": "StartupCo",
                "role": "ML Engineer",
                "type": "employee",
                "location": "NYC",
                "start_date": "2021-06",
                "end_date": "2022-12",
                "short_description": "ML things.",
                "bullets": [
                    {
                        "text": "Built ML pipeline",
                        "metrics": [],
                        "keywords": ["ML"],
                    },
                ],
                "technologies": ["Python"],
            },
        ],
        "projects": [
            {
                "id": "project1",
                "name": "TestProject",
                "tagline": "A test project",
                "description": "Description of test project.",
                "repo_url": "https://github.com/testuser/testproject",
                "status": "active",
                "visibility": "public",
                "pinned": True,
                "highlights": ["Feature A", "Feature B"],
                "technologies": ["Python", "Docker"],
                "topics": ["test"],
            },
        ],
        "skills": {
            "categories": [
                {
                    "name": "Programming",
                    "skills": [
                        {"name": "Python", "proficiency": "expert", "years": 5},
                        {"name": "Go", "proficiency": "proficient", "years": 2},
                    ],
                },
            ],
            "linkedin_skills": {
                "primary": ["Python"],
                "secondary": ["Go"],
            },
        },
        "education": [
            {
                "institution": "Test University",
                "degree": "B.Sc. Computer Science",
                "program": "CS",
                "start_date": "2017",
                "end_date": "2021",
                "location": "Test City",
                "highlights": ["Dean's List"],
            },
        ],
        "github_content": {
            "connect_interests": [
                "Open to **Backend** or **ML** roles",
                "Interested in **open-source**",
            ],
            "footer_quote": "Ship it.",
        },
        "website_content": {
            "what_i_do": "I build test systems.",
            "current_focus": ["Focus A", "Focus B"],
        },
    }

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    profile_path = config_dir / "master_profile.yaml"
    with open(profile_path, "w") as f:
        yaml.dump(profile, f)

    return profile


@pytest.fixture()
def manager(tmp_path: Path, minimal_profile: dict) -> PlatformSyncManager:  # noqa: ARG001
    """Create a PlatformSyncManager pointing at tmp_path."""
    return PlatformSyncManager(project_root=str(tmp_path))


class TestSyncProjectsSection:
    def test_replaces_projects_section(self, manager: PlatformSyncManager) -> None:
        """Projects section should be replaced between markers."""
        content = textwrap.dedent("""\
            %-----------PROJECTS-----------
            \\section{Projects}
            OLD CONTENT HERE
            %-----------EDUCATION-----------
            \\section{Education}
        """)
        result = manager._sync_projects_section(content)
        assert "OLD CONTENT HERE" not in result
        assert "TestProject" in result
        assert "Python, Docker" in result
        assert "%-----------EDUCATION-----------" in result

    def test_empty_projects(self, tmp_path: Path) -> None:
        """Empty projects list should leave content unchanged."""
        config_dir = tmp_path / "config"
        config_dir.mkdir(exist_ok=True)
        profile = {"projects": []}
        with open(config_dir / "master_profile.yaml", "w") as f:
            yaml.dump(profile, f)

        mgr = PlatformSyncManager(project_root=str(tmp_path))
        content = "ORIGINAL CONTENT"
        assert mgr._sync_projects_section(content) == content

    def test_latex_escaping(self, manager: PlatformSyncManager) -> None:
        """Special characters should be escaped in LaTeX output."""
        manager.profile["projects"] = [
            {
                "id": "p1",
                "name": "R&D Project",
                "tagline": "Test",
                "description": "Desc",
                "highlights": ["100% coverage"],
                "technologies": ["C++"],
                "pinned": True,
            },
        ]
        content = "%-----------PROJECTS-----------\nOLD\n%-----------EDUCATION-----------\n"
        result = manager._sync_projects_section(content)
        assert r"R\&D Project" in result
        assert r"100\% coverage" in result


class TestSyncExperienceSection:
    def test_replaces_experience_section(self, manager: PlatformSyncManager) -> None:
        """Experience section should be replaced between markers."""
        content = textwrap.dedent("""\
            %-----------EXPERIENCE-----------
            \\section{Experience}
            OLD CONTENT
            %-----------PROJECTS-----------
            \\section{Projects}
        """)
        result = manager._sync_experience_section(content)
        assert "OLD CONTENT" not in result
        assert "Acme Corp" in result
        assert "Senior Engineer" in result
        assert "2023-01 -- Present" in result
        assert "StartupCo" in result
        assert "2021-06 -- 2022-12" in result

    def test_null_end_date_becomes_present(self, manager: PlatformSyncManager) -> None:
        """Null end_date should render as 'Present'."""
        content = "%-----------EXPERIENCE-----------\nOLD\n%-----------PROJECTS-----------\n"
        result = manager._sync_experience_section(content)
        assert "Present" in result

    def test_empty_experience(self, tmp_path: Path) -> None:
        """Empty experience list should leave content unchanged."""
        config_dir = tmp_path / "config"
        config_dir.mkdir(exist_ok=True)
        with open(config_dir / "master_profile.yaml", "w") as f:
            yaml.dump({"experience": []}, f)

        mgr = PlatformSyncManager(project_root=str(tmp_path))
        content = "ORIGINAL"
        assert mgr._sync_experience_section(content) == content


class TestCompileResumePdf:
    def test_graceful_when_pdflatex_missing(self, manager: PlatformSyncManager) -> None:
        """Should return None when pdflatex is not available."""
        # Create a dummy master.tex
        resume_dir = Path(manager.root) / "resume" / "base"
        resume_dir.mkdir(parents=True, exist_ok=True)
        (resume_dir / "master.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\nHi\n\\end{document}"
        )

        with patch("subprocess.run", side_effect=FileNotFoundError("pdflatex not found")):
            result = manager._compile_resume_pdf()
        assert result is None

    def test_returns_none_when_no_tex_file(self, manager: PlatformSyncManager) -> None:
        """Should return None when master.tex doesn't exist."""
        result = manager._compile_resume_pdf()
        assert result is None


class TestUpdateLatexHeadline:
    def test_headline_replacement(self, manager: PlatformSyncManager) -> None:
        """Should replace textbf headline with textbullet pattern."""
        content = r"\textbf{Old Role \textbullet{} Old Specialty}"
        result = manager._update_latex_headline(content, "New Role • New Specialty")
        assert "New Role" in result
        assert "Old Role" not in result


class TestGitHubConnectInterests:
    def test_profile_driven_connect_interests(self, manager: PlatformSyncManager) -> None:
        """GitHub README should use profile-driven connect interests."""
        readme = manager._generate_github_readme()
        assert "Open to **Backend** or **ML** roles" in readme
        assert "Interested in **open-source**" in readme

    def test_default_connect_interests(self, tmp_path: Path) -> None:
        """Should use defaults when no github_content in profile."""
        config_dir = tmp_path / "config"
        config_dir.mkdir(exist_ok=True)
        profile = {
            "personal": {
                "name": {"full": "X", "first": "X", "last": "X"},
                "tagline": "T",
                "headlines": {"resume": "R", "linkedin": "L", "github": "G", "website": "W"},
                "contact": {"email": "x@x.com", "phone": "0", "location": "R", "timezone": "UTC"},
                "social": {
                    "linkedin": "https://linkedin.com/in/x",
                    "github": "https://github.com/x",
                },
                "languages": [],
            },
            "summaries": {"github": "Summary"},
            "skills": {"categories": []},
        }
        with open(config_dir / "master_profile.yaml", "w") as f:
            yaml.dump(profile, f)

        mgr = PlatformSyncManager(project_root=str(tmp_path))
        readme = mgr._generate_github_readme()
        # Should have fallback interests
        assert "Let's Connect" in readme


class TestGitHubFooterQuote:
    def test_profile_driven_footer_quote(self, manager: PlatformSyncManager) -> None:
        """GitHub README should use profile-driven footer quote."""
        readme = manager._generate_github_readme()
        assert "Ship it." in readme


class TestHomepageCurrentFocus:
    def test_profile_driven_current_focus(self, tmp_path: Path, minimal_profile: dict) -> None:  # noqa: ARG002
        """Website homepage should use profile-driven current focus items."""
        from scripts.website.generator import WebsiteGenerator

        profile_path = tmp_path / "config" / "master_profile.yaml"
        gen = WebsiteGenerator(profile_path=str(profile_path))
        homepage = gen.generate_homepage_content()
        assert "Focus A" in homepage
        assert "Focus B" in homepage
