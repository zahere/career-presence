#!/usr/bin/env python3
"""
Resume Variant Generator
Creates tailored resume variants based on job analysis
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ResumeVariant:
    """Represents a tailored resume variant"""

    job_id: str
    company: str
    role: str
    base_resume: str
    variant_path: str
    pdf_path: str
    tailoring_applied: list[str]
    keywords_included: list[str]
    created_at: str


class ResumeTailor:
    """
    Generates tailored resume variants from base LaTeX resume
    """

    _DEFAULT_SUMMARIES: dict[str, str] = {
        "ai_engineer": r"""\small{AI Infrastructure Engineer specializing in production-grade multi-agent systems and enterprise AI platforms. Built enterprise platforms with composable patterns and integrated services, demonstrating expertise in agentic workflows, service mesh architecture, and LLMOps at scale. Proven track record building MLOps infrastructure and deploying AI systems in regulated environments with rigorous security requirements. Combines systems thinking with deep technical expertise to deliver scalable, production-ready AI platforms.}""",
        "ml_engineer": r"""\small{Machine Learning Engineer with expertise in building production ML systems at scale. Led development of multi-agent LLM systems achieving 38\% improvement in behavioral realism and 91\% trajectory accuracy. Experienced in MLOps pipeline design, model serving infrastructure, and real-time inference optimization. Combines research engineering background with practical systems deployment experience.}""",
        "platform_engineer": r"""\small{Platform Engineer specializing in ML infrastructure and distributed systems. Architected 4-tier service mesh with 27 integrated services, achieving <150ms p99 latency supporting 100+ concurrent agents. Expert in Kubernetes, CI/CD automation, and cloud-native architectures (AWS, GCP, Azure). Track record of reducing deployment cycles from hours to minutes while maintaining enterprise-grade security and compliance.}""",
        "research_engineer": r"""\small{Research Engineer bridging academic rigor with production systems. Building protocol-native multi-agent coordination frameworks exploring token efficiency and mesh-native coordination. Background in experimental design, benchmarking, and systematic evaluation of ML systems. Combines research methodology with practical engineering to deliver reproducible, publishable results.}""",
    }

    _DEFAULT_HEADLINES: dict[str, str] = {
        "ai engineer": "AI Infrastructure Engineer • Multi-Agent Systems Architect",
        "ml engineer": "Machine Learning Engineer • AI Systems Builder",
        "platform engineer": "Platform Engineer • ML Infrastructure Specialist",
        "research engineer": "Research Engineer • AI Systems & Multi-Agent Coordination",
        "staff engineer": "Staff Engineer • AI Infrastructure",
        "founding engineer": "Founding Engineer • AI/ML Systems",
    }

    def __init__(
        self,
        base_resume_path: str = "resume/base/master.tex",
        variants_dir: str = "resume/variants",
        exports_dir: str = "resume/exports",
        profile_path: str = "config/master_profile.yaml",
    ):
        self.base_resume_path = Path(base_resume_path)
        self.variants_dir = Path(variants_dir)
        self.exports_dir = Path(exports_dir)
        self.profile = self._load_profile(profile_path)

        # Ensure directories exist
        self.variants_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def _load_profile(self, profile_path: str) -> dict[str, Any]:
        """Load master profile for dynamic content."""
        path = Path(profile_path)
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        return {}

    def generate_variant(
        self, job_analysis: dict[str, Any], customizations: dict[str, Any] | None = None
    ) -> ResumeVariant:
        """
        Generate a tailored resume variant for a specific job

        Args:
            job_analysis: Output from JobAnalyzer
            customizations: Optional manual overrides
        """
        # Create variant directory
        variant_name = self._generate_variant_name(job_analysis)
        variant_dir = self.variants_dir / variant_name
        variant_dir.mkdir(parents=True, exist_ok=True)

        # Copy base resume and ensure it's writable
        variant_tex = variant_dir / f"{variant_name}.tex"
        shutil.copy(self.base_resume_path, variant_tex)
        variant_tex.chmod(0o644)  # Ensure writable

        # Apply tailoring
        tailoring_applied = []

        # 1. Tailor professional summary
        self._tailor_summary(variant_tex, job_analysis)
        tailoring_applied.append("professional_summary")

        # 2. Reorder experience bullets
        self._reorder_experience(variant_tex, job_analysis)
        tailoring_applied.append("experience_bullets")

        # 3. Adjust skills section
        self._adjust_skills(variant_tex, job_analysis)
        tailoring_applied.append("skills_section")

        # 4. Update headline/title if needed
        self._update_headline(variant_tex, job_analysis)
        tailoring_applied.append("headline")

        # 5. Apply any manual customizations
        if customizations:
            self._apply_customizations(variant_tex, customizations)
            tailoring_applied.append("manual_customizations")

        # Compile to PDF
        pdf_path = self._compile_latex(variant_tex)

        return ResumeVariant(
            job_id=job_analysis.get("job_id", ""),
            company=job_analysis.get("company", ""),
            role=job_analysis.get("role", ""),
            base_resume=str(self.base_resume_path),
            variant_path=str(variant_tex),
            pdf_path=str(pdf_path) if pdf_path else "",
            tailoring_applied=tailoring_applied,
            keywords_included=job_analysis.get("keywords", []),
            created_at=datetime.now().isoformat(),
        )

    def _generate_variant_name(self, job_analysis: dict[str, Any]) -> str:
        """Generate a unique variant name"""
        company = job_analysis.get("company", "unknown").lower()
        company = re.sub(r"[^a-z0-9]", "_", company)

        role = job_analysis.get("role", "engineer").lower()
        role = re.sub(r"[^a-z0-9]", "_", role)[:20]

        date = datetime.now().strftime("%Y%m%d")

        return f"{company}_{role}_{date}"

    def _tailor_summary(self, tex_file: Path, job_analysis: dict[str, Any]) -> None:
        """
        Tailor the professional summary to match job requirements
        """
        with open(tex_file) as f:
            content = f.read()

        # Find the professional summary section
        summary_pattern = r"(\\section\{Professional Summary\}\s*)(.*?)(\n%-)"
        match = re.search(summary_pattern, content, re.DOTALL)

        if not match:
            return

        # Generate tailored summary based on job keywords
        keywords = job_analysis.get("keywords", [])
        role = job_analysis.get("role", "")
        company = job_analysis.get("company", "")

        # Build tailored summary
        tailored_summary = self._build_tailored_summary(keywords, role, company)

        # Replace in content
        new_content = content[: match.start(2)] + tailored_summary + content[match.end(2) :]

        with open(tex_file, "w") as f:
            f.write(new_content)

    def _build_tailored_summary(self, keywords: list[str], role: str, _company: str) -> str:
        """Build a tailored professional summary using role and keywords context."""

        # Load summaries from profile, falling back to class defaults
        profile_summaries = self.profile.get("resume_content", {}).get("summaries_by_role", {})

        # Wrap profile summaries in LaTeX \small{} if they don't already have it
        summaries: dict[str, str] = {}
        for key, default in self._DEFAULT_SUMMARIES.items():
            profile_val = profile_summaries.get(key)
            if profile_val:
                # Wrap in \small{} for LaTeX if not already wrapped
                if not profile_val.strip().startswith(r"\small{"):
                    # Escape LaTeX special chars in profile text
                    profile_val = profile_val.replace("%", r"\%")
                    profile_val = r"\small{" + profile_val.strip() + "}"
                summaries[key] = profile_val
            else:
                summaries[key] = default

        # Use keywords to influence template selection when role title is ambiguous
        kw_lower = {kw.lower() for kw in keywords}
        role_lower = role.lower()

        if any(kw in role_lower for kw in ["ai", "ml", "machine learning", "llm"]):
            if "research" in role_lower or kw_lower & {"research", "papers", "experiments"}:
                return summaries["research_engineer"]
            elif (
                "platform" in role_lower
                or "infrastructure" in role_lower
                or kw_lower & {"kubernetes", "devops", "terraform", "platform"}
            ):
                return summaries["platform_engineer"]
            else:
                return summaries["ai_engineer"]
        elif (
            "platform" in role_lower
            or "infrastructure" in role_lower
            or kw_lower & {"kubernetes", "devops", "terraform", "ci/cd", "helm"}
        ):
            return summaries["platform_engineer"]
        elif kw_lower & {"research", "papers", "phd", "publications"}:
            return summaries["research_engineer"]
        elif kw_lower & {"mlops", "model serving", "feature engineering"}:
            return summaries["ml_engineer"]
        else:
            return summaries["ai_engineer"]  # Default

    def _reorder_experience(self, tex_file: Path, job_analysis: dict[str, Any]) -> None:
        """
        Reorder experience bullet points based on job relevance.
        Scores each bullet based on keyword matches and moves high-scoring bullets up.
        """
        with open(tex_file) as f:
            content = f.read()

        keywords = [kw.lower() for kw in job_analysis.get("keywords", [])]
        if not keywords:
            return

        # Find experience sections with bullet points
        # Pattern matches \item entries within itemize environments
        item_pattern = r"(\\item\s+)([^\n]+(?:\n(?!\s*\\item|\s*\\end).*)*)"

        def score_bullet(bullet_text: str) -> int:
            """Score a bullet based on keyword matches."""
            bullet_lower = bullet_text.lower()
            return sum(1 for kw in keywords if kw in bullet_lower)

        def reorder_items_in_section(section_match: re.Match[str]) -> str:
            """Reorder items within a matched section."""
            section_text = section_match.group(0)

            # Extract all items
            items = re.findall(item_pattern, section_text)
            if len(items) <= 1:
                return section_text

            # Score and sort items (stable sort preserves order for equal scores)
            scored_items = [(score_bullet(text), prefix, text) for prefix, text in items]
            scored_items.sort(key=lambda x: -x[0])  # Descending by score

            # Rebuild section with reordered items
            new_section = section_text
            for i, (_, prefix, text) in enumerate(items):
                old_item = f"{prefix}{text}"
                new_score, new_prefix, new_text = scored_items[i]
                new_item = f"{new_prefix}{new_text}"
                new_section = new_section.replace(old_item, new_item, 1)

            return new_section

        # Find itemize environments in experience section
        exp_pattern = r"(\\section\{(?:Experience|Professional Experience|Work Experience)\}.*?)(\\begin\{itemize\}.*?\\end\{itemize\})"

        matches = list(re.finditer(exp_pattern, content, re.DOTALL))
        if matches:
            for match in reversed(matches):  # Process in reverse to preserve positions
                original = match.group(2)
                reordered = reorder_items_in_section(match)
                if reordered != original:
                    content = content[: match.start(2)] + reordered + content[match.end(2) :]

            with open(tex_file, "w") as f:
                f.write(content)

    def _adjust_skills(self, tex_file: Path, job_analysis: dict[str, Any]) -> None:
        """
        Adjust skills section ordering based on job keywords.
        Reorders skill categories to prioritize those matching JD keywords.
        """
        with open(tex_file) as f:
            content = f.read()

        keywords = [kw.lower() for kw in job_analysis.get("keywords", [])]
        if not keywords:
            return

        # Find skills section - handle various LaTeX patterns
        # Pattern 1: \textbf{Category}{: skills}
        pattern1 = r"\\textbf\{([^}]+)\}\s*\{:\s*([^}]+)\}"
        # Pattern 2: \item \textbf{Category}: skills
        pattern2 = r"\\item\s*\\textbf\{([^}]+)\}:\s*([^\n\\]+)"

        # Try pattern 1 first
        skill_matches = list(re.finditer(pattern1, content))
        pattern_used = 1

        if not skill_matches:
            # Try pattern 2
            skill_matches = list(re.finditer(pattern2, content))
            pattern_used = 2

        if not skill_matches:
            return

        # Score each skill category
        scored_skills = []
        for match in skill_matches:
            category_name = match.group(1)
            skill_list = match.group(2)
            score = sum(1 for kw in keywords if kw in skill_list.lower())
            scored_skills.append((score, category_name, skill_list, match))

        # Sort by score (descending)
        scored_skills.sort(key=lambda x: -x[0])

        # Only reorder if there's meaningful score difference
        if scored_skills[0][0] == scored_skills[-1][0]:
            return  # All same score, no reordering needed

        # Build reordered content list
        new_order = []

        for _score, name, skills, _ in scored_skills:
            if pattern_used == 1:
                new_order.append(f"\\textbf{{{name}}}{{: {skills}}}")
            else:
                new_order.append(f"\\item \\textbf{{{name}}}: {skills}")

        # Replace in content (process in reverse to preserve positions)
        for i, match in enumerate(reversed(skill_matches)):
            idx = len(skill_matches) - 1 - i
            new_content = new_order[idx]
            content = content[: match.start()] + new_content + content[match.end() :]

        with open(tex_file, "w") as f:
            f.write(content)

    def _update_headline(self, tex_file: Path, job_analysis: dict[str, Any]) -> None:
        """
        Update the headline/title to match the role
        """
        with open(tex_file) as f:
            content = f.read()

        role = job_analysis.get("role", "")

        # Load headlines from profile, falling back to class defaults
        profile_headlines = self.profile.get("resume_content", {}).get("headlines_by_role", {})
        headlines: dict[str, str] = {}
        for key, default in self._DEFAULT_HEADLINES.items():
            headlines[key] = profile_headlines.get(key.replace(" ", "_"), default)

        role_lower = role.lower()
        new_headline = headlines.get(role_lower)

        if not new_headline:
            # Try partial matches
            for key, headline in headlines.items():
                if key in role_lower or any(word in role_lower for word in key.split()):
                    new_headline = headline
                    break

        if new_headline:
            # Replace headline in LaTeX
            headline_pattern = r"(\\small \\textbf\{)([^}]+)(\})"
            content = re.sub(headline_pattern, rf"\1{new_headline}\3", content, count=1)

            with open(tex_file, "w") as f:
                f.write(content)

    def _apply_customizations(self, tex_file: Path, customizations: dict[str, Any]) -> None:
        """Apply manual customizations"""
        with open(tex_file) as f:
            content = f.read()

        # Apply find-replace customizations
        for find, replace in customizations.get("replacements", {}).items():
            content = content.replace(find, replace)

        with open(tex_file, "w") as f:
            f.write(content)

    def _compile_latex(self, tex_file: Path) -> Path | None:
        """
        Compile LaTeX to PDF

        Returns:
            Path to PDF file if successful, None otherwise
        """
        try:
            # Run pdflatex twice for proper cross-references
            for _ in range(2):
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", tex_file.name],
                    cwd=tex_file.parent,
                    capture_output=True,
                    timeout=60,
                )

            pdf_name = tex_file.stem + ".pdf"
            pdf_path = tex_file.parent / pdf_name

            if pdf_path.exists():
                # Copy to exports directory
                export_path = self.exports_dir / pdf_name
                shutil.copy(pdf_path, export_path)
                return export_path

        except subprocess.TimeoutExpired:
            print(f"LaTeX compilation timed out for {tex_file}")
        except FileNotFoundError:
            print("pdflatex not found. Please install TeX Live or similar.")
        except Exception as e:
            print(f"LaTeX compilation failed: {e}")

        return None

    def save_variant_metadata(self, variant: ResumeVariant) -> None:
        """Save variant metadata for tracking"""
        metadata_path = Path(variant.variant_path).parent / "metadata.json"

        with open(metadata_path, "w") as f:
            json.dump(
                {
                    "job_id": variant.job_id,
                    "company": variant.company,
                    "role": variant.role,
                    "base_resume": variant.base_resume,
                    "variant_path": variant.variant_path,
                    "pdf_path": variant.pdf_path,
                    "tailoring_applied": variant.tailoring_applied,
                    "keywords_included": variant.keywords_included,
                    "created_at": variant.created_at,
                },
                f,
                indent=2,
            )


def main() -> None:
    """Example usage"""
    tailor = ResumeTailor()

    # Example job analysis
    job_analysis = {
        "job_id": "12345",
        "company": "Anthropic",
        "role": "AI Research Engineer",
        "keywords": [
            "multi-agent",
            "llm",
            "python",
            "pytorch",
            "distributed systems",
            "kubernetes",
        ],
        "matched_skills": ["python", "kubernetes", "llm"],
        "tailoring_notes": [
            "Emphasize multi-agent system work",
            "Highlight production deployment experience",
        ],
    }

    # Generate variant
    variant = tailor.generate_variant(job_analysis)

    print(f"Generated variant: {variant.variant_path}")
    print(f"PDF path: {variant.pdf_path}")
    print(f"Tailoring applied: {variant.tailoring_applied}")

    # Save metadata
    tailor.save_variant_metadata(variant)


if __name__ == "__main__":
    main()
