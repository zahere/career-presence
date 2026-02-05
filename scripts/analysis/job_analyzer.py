#!/usr/bin/env python3
"""
Job Description Analysis Module
Extracts requirements, keywords, and calculates match scores
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml


@dataclass
class JobRequirement:
    text: str
    category: str  # must_have, nice_to_have
    matched: bool = False
    match_source: Optional[str] = None


@dataclass
class JobAnalysis:
    job_id: str
    company: str
    role: str
    url: str
    location: str
    remote_policy: str
    salary_range: Optional[str]
    
    # Extracted requirements
    must_have: List[JobRequirement]
    nice_to_have: List[JobRequirement]
    
    # Keywords for ATS
    keywords: List[str]
    
    # Matching
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    
    # Recommendations
    tailoring_notes: List[str]
    
    # Metadata
    analyzed_at: str
    raw_description: str


class JobAnalyzer:
    """Analyzes job descriptions and calculates match scores"""
    
    # Keywords indicating requirements
    MUST_HAVE_INDICATORS = [
        "required", "must have", "minimum", "essential",
        "mandatory", "necessary", "need to have"
    ]
    
    NICE_TO_HAVE_INDICATORS = [
        "preferred", "nice to have", "bonus", "plus",
        "ideally", "desirable", "advantageous"
    ]
    
    # Common skills to extract
    TECH_SKILLS = [
        # Languages
        "python", "go", "rust", "c++", "typescript", "java", "scala",
        # ML/AI
        "pytorch", "tensorflow", "jax", "transformers", "llm", "nlp",
        "machine learning", "deep learning", "reinforcement learning",
        "rag", "fine-tuning", "prompt engineering", "langchain",
        # Infrastructure
        "kubernetes", "docker", "helm", "terraform", "aws", "gcp", "azure",
        "ci/cd", "mlops", "devops", "kafka", "redis",
        # Databases
        "postgresql", "mongodb", "elasticsearch", "vector database",
        "pinecone", "weaviate", "qdrant",
        # Concepts
        "distributed systems", "microservices", "api design",
        "system design", "data pipelines", "etl"
    ]
    
    EXPERIENCE_PATTERNS = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)",
        r"(?:experience|exp)\s*(?:of)?\s*(\d+)\+?\s*(?:years?|yrs?)",
    ]
    
    def __init__(self, profile_path: str = "config/master_profile.yaml"):
        self.profile = self._load_profile(profile_path)
        
    def _load_profile(self, path: str) -> Dict[str, Any]:
        """Load user profile for matching"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def analyze(self, job_data: Dict[str, Any]) -> JobAnalysis:
        """
        Analyze a job description and return structured analysis
        
        Args:
            job_data: Dictionary containing:
                - id: Job identifier
                - company: Company name
                - title: Job title
                - url: Job posting URL
                - description: Full job description text
                - location: Job location
                - salary: Optional salary range
        """
        description = job_data.get("description", "").lower()
        
        # Extract requirements
        must_have = self._extract_requirements(description, "must_have")
        nice_to_have = self._extract_requirements(description, "nice_to_have")
        
        # Extract keywords
        keywords = self._extract_keywords(description)
        
        # Calculate match score
        matched_skills, missing_skills = self._match_skills(keywords)
        match_score = self._calculate_match_score(must_have, nice_to_have, matched_skills)
        
        # Generate tailoring recommendations
        tailoring_notes = self._generate_tailoring_notes(
            must_have, nice_to_have, matched_skills, missing_skills
        )
        
        return JobAnalysis(
            job_id=job_data.get("id", ""),
            company=job_data.get("company", ""),
            role=job_data.get("title", ""),
            url=job_data.get("url", ""),
            location=job_data.get("location", ""),
            remote_policy=self._extract_remote_policy(description),
            salary_range=job_data.get("salary"),
            must_have=must_have,
            nice_to_have=nice_to_have,
            keywords=keywords,
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            tailoring_notes=tailoring_notes,
            analyzed_at=datetime.now().isoformat(),
            raw_description=job_data.get("description", "")
        )
    
    def _extract_requirements(self, text: str, category: str) -> List[JobRequirement]:
        """Extract requirements from job description"""
        requirements = []
        
        # Split into sentences/bullets
        lines = re.split(r'[•\n\r]+', text)
        
        indicators = (
            self.MUST_HAVE_INDICATORS if category == "must_have" 
            else self.NICE_TO_HAVE_INDICATORS
        )
        
        in_requirements_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if we're in a requirements section
            if any(ind in line for ind in indicators):
                in_requirements_section = True
                
            # Look for bullet points or numbered items
            if in_requirements_section and (
                line.startswith(('-', '*', '•')) or
                re.match(r'^\d+\.', line)
            ):
                clean_line = re.sub(r'^[-*•\d.]+\s*', '', line).strip()
                if len(clean_line) > 10:  # Filter out short fragments
                    requirements.append(JobRequirement(
                        text=clean_line,
                        category=category
                    ))
        
        return requirements
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant technical keywords"""
        keywords = []
        
        for skill in self.TECH_SKILLS:
            if skill in text:
                keywords.append(skill)
        
        # Extract years of experience
        for pattern in self.EXPERIENCE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                keywords.append(f"{match}+ years experience")
        
        return list(set(keywords))
    
    def _extract_remote_policy(self, text: str) -> str:
        """Determine remote work policy"""
        if "fully remote" in text or "100% remote" in text:
            return "fully_remote"
        elif "hybrid" in text:
            return "hybrid"
        elif "remote" in text:
            return "remote_friendly"
        elif "on-site" in text or "onsite" in text or "in-office" in text:
            return "onsite"
        return "unknown"
    
    def _match_skills(self, keywords: List[str]) -> tuple:
        """Match extracted keywords against user profile"""
        user_skills = []
        
        # Flatten user skills from profile
        for category in self.profile.get("skills_by_category", {}).values():
            for level in ["expert", "proficient", "familiar"]:
                user_skills.extend(category.get(level, []))
        
        user_skills_lower = [s.lower() for s in user_skills]
        
        matched = []
        missing = []
        
        for keyword in keywords:
            if any(keyword in skill for skill in user_skills_lower):
                matched.append(keyword)
            else:
                missing.append(keyword)
        
        return matched, missing
    
    def _calculate_match_score(
        self, 
        must_have: List[JobRequirement],
        nice_to_have: List[JobRequirement],
        matched_skills: List[str]
    ) -> float:
        """
        Calculate overall match score (0-100)
        
        Weighting:
        - Must-have requirements: 60%
        - Nice-to-have requirements: 20%
        - Keyword matches: 20%
        """
        # Must-have score
        if must_have:
            must_have_matches = sum(1 for r in must_have if r.matched)
            must_have_score = (must_have_matches / len(must_have)) * 60
        else:
            must_have_score = 60  # No explicit must-haves = full score
        
        # Nice-to-have score
        if nice_to_have:
            nice_to_have_matches = sum(1 for r in nice_to_have if r.matched)
            nice_to_have_score = (nice_to_have_matches / len(nice_to_have)) * 20
        else:
            nice_to_have_score = 10  # Partial score if not specified
        
        # Keyword match score (based on JD keywords extracted)
        # Note: jd_keywords would be passed from analyze() - using matched_skills + missing as proxy
        keyword_score = min(20, len(matched_skills) * 2)  # 2 points per match, max 20
        
        return round(must_have_score + nice_to_have_score + keyword_score, 1)
    
    def _generate_tailoring_notes(
        self,
        must_have: List[JobRequirement],
        nice_to_have: List[JobRequirement],
        matched_skills: List[str],
        missing_skills: List[str]
    ) -> List[str]:
        """Generate actionable notes for resume tailoring"""
        notes = []
        
        # Priority keywords to include
        if matched_skills:
            notes.append(f"INCLUDE these keywords prominently: {', '.join(matched_skills[:5])}")
        
        # Skills gaps to address
        if missing_skills:
            notes.append(f"Consider addressing: {', '.join(missing_skills[:3])}")
        
        # Experience emphasis
        notes.append("Lead with AgentiCraft experience for multi-agent/LLM roles")
        notes.append("Emphasize infrastructure work for platform roles")
        
        return notes
    
    def save_analysis(self, analysis: JobAnalysis, output_dir: str = "jobs/analyzed"):
        """Save analysis to JSON file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{analysis.company}_{analysis.job_id}_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(asdict(analysis), f, indent=2)
        
        return filepath


def main():
    """Example usage"""
    analyzer = JobAnalyzer()
    
    # Example job data
    sample_job = {
        "id": "12345",
        "company": "Anthropic",
        "title": "AI Research Engineer",
        "url": "https://boards.greenhouse.io/anthropic/jobs/12345",
        "location": "San Francisco, CA (Remote OK)",
        "salary": "$200,000 - $350,000",
        "description": """
        About the role:
        We're looking for an AI Research Engineer to help build the next generation
        of AI systems. You'll work on multi-agent systems, LLM infrastructure, and
        alignment research.
        
        Requirements:
        • 5+ years of experience in machine learning or AI
        • Expert-level Python programming
        • Experience with PyTorch or JAX
        • Strong background in distributed systems
        • Experience with LLMs and prompt engineering
        
        Nice to have:
        • PhD in ML, CS, or related field
        • Publications in top venues (NeurIPS, ICML)
        • Experience with Kubernetes and MLOps
        • Rust or Go programming experience
        
        This is a fully remote position.
        """
    }
    
    analysis = analyzer.analyze(sample_job)
    print(f"Match Score: {analysis.match_score}%")
    print(f"Matched Skills: {analysis.matched_skills}")
    print(f"Missing Skills: {analysis.missing_skills}")
    print(f"Tailoring Notes: {analysis.tailoring_notes}")
    
    # Save analysis
    filepath = analyzer.save_analysis(analysis)
    print(f"Analysis saved to: {filepath}")


if __name__ == "__main__":
    main()
