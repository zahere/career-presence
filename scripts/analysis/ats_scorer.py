#!/usr/bin/env python3
"""
ATS (Applicant Tracking System) Scorer
Calculates how well a resume will perform with automated screening systems.

Algorithm:
- 40% Keyword Match
- 20% Section Presence
- 20% Quantifiable Metrics
- 20% Formatting Quality
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ATSScore:
    """ATS scoring result"""

    total_score: int
    keyword_score: float
    section_score: float
    metrics_score: float
    formatting_score: float

    matched_keywords: list[str]
    missing_keywords: list[str]
    sections_found: list[str]
    sections_missing: list[str]
    metrics_found: list[str]
    formatting_issues: list[str]

    recommendation: str  # "auto_apply", "ready", "needs_review", "regenerate"


class ATSScorer:
    """
    Scores resumes against job descriptions for ATS compatibility.
    Target: 80%+ for auto-apply consideration.
    """

    # Standard ATS-friendly section names
    REQUIRED_SECTIONS = [
        "experience",
        "work experience",
        "professional experience",
        "education",
        "skills",
        "technical skills",
        "projects",
        "summary",
        "professional summary",
    ]

    # Technical keyword patterns
    TECH_KEYWORDS = {
        # Languages
        "python",
        "go",
        "golang",
        "rust",
        "c++",
        "cpp",
        "java",
        "scala",
        "typescript",
        "javascript",
        "sql",
        "bash",
        # ML/AI
        "machine learning",
        "deep learning",
        "neural network",
        "llm",
        "large language model",
        "nlp",
        "natural language processing",
        "computer vision",
        "reinforcement learning",
        "transformer",
        "pytorch",
        "tensorflow",
        "jax",
        "keras",
        "hugging face",
        "fine-tuning",
        "fine tuning",
        "lora",
        "qlora",
        "peft",
        "rag",
        "retrieval augmented",
        "prompt engineering",
        "agent",
        "multi-agent",
        "agentic",
        # Infrastructure
        "kubernetes",
        "k8s",
        "docker",
        "helm",
        "terraform",
        "aws",
        "gcp",
        "azure",
        "cloud",
        "ci/cd",
        "cicd",
        "github actions",
        "argocd",
        "jenkins",
        "mlops",
        "devops",
        "sre",
        # Data
        "postgresql",
        "postgres",
        "mysql",
        "mongodb",
        "redis",
        "elasticsearch",
        "kafka",
        "spark",
        "vector database",
        "pinecone",
        "weaviate",
        "qdrant",
        "chroma",
        # Concepts
        "distributed systems",
        "microservices",
        "api",
        "rest",
        "system design",
        "scalability",
        "performance",
        "observability",
        "monitoring",
        "prometheus",
        "grafana",
        "opentelemetry",
        "tracing",
    }

    # Metric patterns to look for
    METRIC_PATTERNS = [
        r"\d+%",  # Percentages: 50%, 32%
        r"\d+x",  # Multipliers: 2.1x, 3x
        r"\$[\d,]+(?:k|K|m|M)?",  # Money: $1,200, $50K
        r"\d+\+?\s*(?:years?|yrs?)",  # Years: 5+ years
        r"<\d+\s*(?:ms|s|min|minutes?)",  # Latency: <150ms, <2 minutes
        r"\d+,?\d*\+?\s*(?:users?|customers?|agents?|requests?)",  # Scale
        r"\d+\s*(?:layers?|services?|patterns?|providers?)",  # Counts
    ]

    def __init__(self, keywords_db_path: str | None = None) -> None:
        """
        Initialize scorer with optional custom keywords database.

        Args:
            keywords_db_path: Path to JSON file with additional keywords by role
        """
        self.custom_keywords: dict[str, set[str]] = {
            "ai_engineer": {
                "multi-agent",
                "agentic",
                "llm orchestration",
                "langchain",
                "llamaindex",
                "prompt optimization",
            },
            "platform_engineer": {
                "platform engineering",
                "service mesh",
                "infrastructure as code",
                "observability",
                "sre",
            },
            "ml_engineer": {
                "model deployment",
                "feature engineering",
                "model monitoring",
                "experiment tracking",
                "model serving",
            },
            "research_engineer": {
                "research",
                "publications",
                "experiments",
                "benchmarking",
                "ablation",
                "evaluation",
            },
        }
        if keywords_db_path and Path(keywords_db_path).exists():
            with open(keywords_db_path) as f:
                loaded = json.load(f)
                for role, kws in loaded.items():
                    if role in self.custom_keywords:
                        self.custom_keywords[role].update(kws)
                    else:
                        self.custom_keywords[role] = set(kws)

    def score(
        self, resume_text: str, job_description: str, role_type: str | None = None
    ) -> ATSScore:
        """
        Calculate ATS score for resume against job description.

        Args:
            resume_text: Full text extracted from resume PDF
            job_description: Job description text
            role_type: Optional role type for custom keyword weighting

        Returns:
            ATSScore with detailed breakdown
        """
        # Normalize texts
        resume_lower = resume_text.lower()
        jd_lower = job_description.lower()

        # 1. Keyword Match (40 points)
        keyword_result = self._score_keywords(resume_lower, jd_lower, role_type)

        # 2. Section Presence (20 points)
        section_result = self._score_sections(resume_lower)

        # 3. Quantifiable Metrics (20 points)
        metrics_result = self._score_metrics(resume_text)

        # 4. Formatting Quality (20 points)
        formatting_result = self._score_formatting(resume_text)

        # Calculate total
        total_score = int(
            keyword_result[0] + section_result[0] + metrics_result[0] + formatting_result[0]
        )

        # Determine recommendation
        if total_score >= 85:
            recommendation = "auto_apply"
        elif total_score >= 80:
            recommendation = "ready"
        elif total_score >= 70:
            recommendation = "needs_review"
        else:
            recommendation = "regenerate"

        return ATSScore(
            total_score=total_score,
            keyword_score=keyword_result[0],
            section_score=section_result[0],
            metrics_score=metrics_result[0],
            formatting_score=formatting_result[0],
            matched_keywords=keyword_result[1],
            missing_keywords=keyword_result[2],
            sections_found=section_result[1],
            sections_missing=section_result[2],
            metrics_found=metrics_result[1],
            formatting_issues=formatting_result[1],
            recommendation=recommendation,
        )

    def _score_keywords(
        self, resume: str, jd: str, role_type: str | None
    ) -> tuple[float, list[str], list[str]]:
        """
        Score keyword match (40 points max).
        """
        # Extract keywords from job description
        jd_keywords = set()

        # Check for technical keywords
        for keyword in self.TECH_KEYWORDS:
            if keyword in jd:
                jd_keywords.add(keyword)

        # Add custom keywords for role type
        if role_type and role_type in self.custom_keywords:
            for keyword in self.custom_keywords[role_type]:
                if keyword.lower() in jd:
                    jd_keywords.add(keyword.lower())

        # Extract any capitalized technical terms (likely important)
        tech_terms = re.findall(r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\b", jd)
        for term in tech_terms:
            if len(term) > 2:  # Skip short acronyms
                jd_keywords.add(term.lower())

        if not jd_keywords:
            return (20.0, [], [])  # Partial score if no keywords detected

        # Check which keywords are in resume
        matched = []
        missing = []

        for keyword in jd_keywords:
            if keyword in resume:
                matched.append(keyword)
            else:
                missing.append(keyword)

        # Calculate score
        match_ratio = len(matched) / len(jd_keywords) if jd_keywords else 0
        score = match_ratio * 40

        return (score, matched, missing)

    def _score_sections(self, resume: str) -> tuple[float, list[str], list[str]]:
        """
        Score section presence (20 points max).
        """
        found = []
        missing = []

        # Group related section names
        section_groups = [
            ["experience", "work experience", "professional experience"],
            ["education", "academic background"],
            ["skills", "technical skills", "core competencies"],
            ["projects", "key projects", "selected projects"],
            ["summary", "professional summary", "profile", "objective"],
        ]

        for group in section_groups:
            group_found = False
            for section_name in group:
                if section_name in resume:
                    found.append(section_name)
                    group_found = True
                    break
            if not group_found:
                missing.append(group[0])  # Report first name in group

        # Calculate score (4 points per section group)
        score = (len(found) / len(section_groups)) * 20

        return (score, found, missing)

    def _score_metrics(self, resume: str) -> tuple[float, list[str]]:
        """
        Score quantifiable metrics (20 points max).
        """
        metrics_found = []

        for pattern in self.METRIC_PATTERNS:
            matches = re.findall(pattern, resume, re.IGNORECASE)
            metrics_found.extend(matches)

        # Deduplicate
        metrics_found = list(set(metrics_found))

        # Score: 2 points per metric, max 20 (10 metrics)
        score = min(len(metrics_found) * 2, 20)

        return (score, metrics_found)

    def _score_formatting(self, resume: str) -> tuple[float, list[str]]:
        """
        Score formatting quality (20 points max).
        """
        issues = []
        score = 20.0

        # Check 1: Text extractability (implied by having text)
        if len(resume.strip()) < 500:
            issues.append("Resume text appears too short or not extractable")
            score -= 10

        # Check 2: No obvious encoding issues
        if "�" in resume or "\\x" in resume:
            issues.append("Encoding issues detected")
            score -= 5

        # Check 3: Reasonable structure (has bullet points or clear sections)
        bullet_patterns = [r"•", r"\\item", r"^\s*[-*]", r"^\s*\d+\."]
        has_bullets = any(re.search(p, resume, re.MULTILINE) for p in bullet_patterns)
        if not has_bullets:
            issues.append("No bullet points detected")
            score -= 3

        # Check 4: Not too much whitespace (suggests tables/columns)
        whitespace_ratio = len(re.findall(r"\s{3,}", resume)) / max(len(resume), 1)
        if whitespace_ratio > 0.1:
            issues.append("Excessive whitespace (possible multi-column layout)")
            score -= 2

        return (max(score, 0), issues)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using pdftotext.
        Falls back to basic extraction if pdftotext unavailable.
        """
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", pdf_path, "-"], capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass  # pdftotext unavailable or timed out; fall back to pypdf

        # Fallback: try PyPDF2 or similar
        try:
            from pypdf import PdfReader

            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            pass  # pypdf not installed

        raise RuntimeError(f"Could not extract text from {pdf_path}")

    def score_pdf(
        self, pdf_path: str, job_description: str, role_type: str | None = None
    ) -> ATSScore:
        """
        Score a PDF resume against a job description.
        """
        resume_text = self.extract_text_from_pdf(pdf_path)
        return self.score(resume_text, job_description, role_type)


def generate_report(score: ATSScore) -> str:
    """Generate human-readable ATS score report."""

    status_emoji = {"auto_apply": "🚀", "ready": "✅", "needs_review": "⚠️", "regenerate": "❌"}

    report = f"""
╔════════════════════════════════════════════════════════════════╗
║                      ATS SCORE REPORT                           ║
╠════════════════════════════════════════════════════════════════╣
║  TOTAL SCORE: {score.total_score}/100 {status_emoji.get(score.recommendation, "")}
║  Recommendation: {score.recommendation.upper()}
╠════════════════════════════════════════════════════════════════╣
║  BREAKDOWN:                                                     ║
║  ├── Keyword Match:    {score.keyword_score:5.1f}/40                           ║
║  ├── Section Presence: {score.section_score:5.1f}/20                           ║
║  ├── Metrics Found:    {score.metrics_score:5.1f}/20                           ║
║  └── Formatting:       {score.formatting_score:5.1f}/20                           ║
╠════════════════════════════════════════════════════════════════╣
║  KEYWORDS:                                                      ║
║  ✅ Matched ({len(score.matched_keywords)}): {", ".join(score.matched_keywords[:5])}{"..." if len(score.matched_keywords) > 5 else ""}
║  ❌ Missing ({len(score.missing_keywords)}): {", ".join(score.missing_keywords[:5])}{"..." if len(score.missing_keywords) > 5 else ""}
╠════════════════════════════════════════════════════════════════╣
║  SECTIONS:                                                      ║
║  ✅ Found: {", ".join(score.sections_found)}
║  ❌ Missing: {", ".join(score.sections_missing) if score.sections_missing else "None"}
╠════════════════════════════════════════════════════════════════╣
║  METRICS FOUND ({len(score.metrics_found)}):                                        ║
║  {", ".join(score.metrics_found[:8])}
╚════════════════════════════════════════════════════════════════╝
"""

    if score.formatting_issues:
        report += "\n⚠️ Formatting Issues:\n"
        for issue in score.formatting_issues:
            report += f"  - {issue}\n"

    return report


def main() -> None:
    """Example usage"""
    scorer = ATSScorer()

    # Example job description
    job_description = """
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

    # Example resume text (would normally extract from PDF)
    resume_text = """
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

    # Score the resume
    result = scorer.score(resume_text, job_description, role_type="ai_engineer")

    # Print report
    print(generate_report(result))


if __name__ == "__main__":
    main()
