#!/usr/bin/env python3
"""
Platform Sync Manager

Synchronizes content across all career platforms from master_profile.yaml:
- Resume (LaTeX)
- LinkedIn Profile
- GitHub Profile README
- Personal Website

Maintains single source of truth with platform-specific transformations.
"""

import yaml
import json
import os
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import subprocess
import shutil


class Platform(Enum):
    RESUME = "resume"
    LINKEDIN = "linkedin"
    GITHUB = "github"
    WEBSITE = "website"
    ALL = "all"


@dataclass
class SyncResult:
    """Result of a sync operation"""
    platform: Platform
    success: bool
    files_updated: List[str]
    errors: List[str]
    timestamp: datetime


class PlatformSyncManager:
    """
    Manages synchronization of career content across platforms.
    """
    
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.profile_path = self.root / "config" / "master_profile.yaml"
        self.profile = self._load_profile()
        self.sync_log: List[SyncResult] = []
        
    def _load_profile(self) -> Dict[str, Any]:
        """Load master profile."""
        with open(self.profile_path) as f:
            return yaml.safe_load(f)
    
    def reload_profile(self):
        """Reload profile from disk."""
        self.profile = self._load_profile()
        
    # ═══════════════════════════════════════════════════════════════════════
    # RESUME SYNC
    # ═══════════════════════════════════════════════════════════════════════
    
    def sync_resume(self) -> SyncResult:
        """
        Sync master profile to LaTeX resume.
        Updates sections while preserving LaTeX formatting.
        """
        errors = []
        files_updated = []
        
        resume_path = self.root / "resume" / "base" / "master.tex"
        
        if not resume_path.exists():
            return SyncResult(
                platform=Platform.RESUME,
                success=False,
                files_updated=[],
                errors=["master.tex not found"],
                timestamp=datetime.now()
            )
        
        try:
            content = resume_path.read_text()
            
            # Update personal info
            personal = self.profile['personal']
            content = self._update_latex_field(content, 'name', personal['name']['full'])
            content = self._update_latex_field(content, 'phone', personal['contact']['phone'])
            content = self._update_latex_field(content, 'email', personal['contact']['email'])
            content = self._update_latex_field(content, 'linkedin', personal['social']['linkedin'])
            content = self._update_latex_field(content, 'github', personal['social']['github'])
            
            # Update headline
            content = self._update_latex_headline(content, personal['headlines']['resume'])
            
            # Backup and save
            backup_path = resume_path.with_suffix('.tex.bak')
            shutil.copy(resume_path, backup_path)
            resume_path.write_text(content)
            
            files_updated.append(str(resume_path))
            
        except Exception as e:
            errors.append(f"Resume sync failed: {str(e)}")
        
        return SyncResult(
            platform=Platform.RESUME,
            success=len(errors) == 0,
            files_updated=files_updated,
            errors=errors,
            timestamp=datetime.now()
        )
    
    def _update_latex_field(self, content: str, field: str, value: str) -> str:
        """Update a LaTeX field definition."""
        # Use re.escape for the field name and proper escaping for \def
        pattern = r'\\def\\' + re.escape(field) + r'\{[^}]*\}'
        replacement = r'\\def\\' + field + '{' + value + '}'
        # Only replace if pattern exists (resume may not use \def macros)
        if re.search(pattern, content):
            return re.sub(pattern, replacement, content)
        return content
    
    def _update_latex_headline(self, content: str, headline: str) -> str:
        """Update the headline/tagline in LaTeX resume."""
        # Look for headline pattern
        pattern = r'\\textbf{[^}]+\\textbullet[^}]+}'
        return re.sub(pattern, f'\\\\textbf{{{headline}}}', content)
    
    # ═══════════════════════════════════════════════════════════════════════
    # LINKEDIN SYNC
    # ═══════════════════════════════════════════════════════════════════════
    
    def sync_linkedin(self) -> SyncResult:
        """
        Sync master profile to LinkedIn content files.
        Generates optimized content for manual or MCP-based update.
        """
        errors = []
        files_updated = []
        
        linkedin_dir = self.root / "linkedin" / "profile"
        linkedin_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            personal = self.profile['personal']
            
            # Generate headline options
            headline_content = self._generate_linkedin_headlines()
            (linkedin_dir / "headlines.md").write_text(headline_content)
            files_updated.append("linkedin/profile/headlines.md")
            
            # Generate about section
            about_content = self.profile['summaries']['linkedin']
            (linkedin_dir / "about.md").write_text(f"# LinkedIn About Section\n\n{about_content}")
            files_updated.append("linkedin/profile/about.md")
            
            # Generate experience descriptions
            exp_content = self._generate_linkedin_experience()
            (linkedin_dir / "experience.md").write_text(exp_content)
            files_updated.append("linkedin/profile/experience.md")
            
            # Generate skills list
            skills_content = self._generate_linkedin_skills()
            (linkedin_dir / "skills.md").write_text(skills_content)
            files_updated.append("linkedin/profile/skills.md")
            
            # Generate sync instructions
            instructions = self._generate_linkedin_instructions()
            (linkedin_dir / "SYNC_INSTRUCTIONS.md").write_text(instructions)
            files_updated.append("linkedin/profile/SYNC_INSTRUCTIONS.md")
            
        except Exception as e:
            errors.append(f"LinkedIn sync failed: {str(e)}")
        
        return SyncResult(
            platform=Platform.LINKEDIN,
            success=len(errors) == 0,
            files_updated=files_updated,
            errors=errors,
            timestamp=datetime.now()
        )
    
    def _generate_linkedin_headlines(self) -> str:
        """Generate LinkedIn headline options."""
        personal = self.profile['personal']
        
        return f"""# LinkedIn Headline Options

**Current Recommended:**
```
{personal['headlines']['linkedin']}
```

**Alternative Options:**

1. **Builder Focus:**
   Building AgentiCraft | AI Infrastructure Engineer | Multi-Agent Systems Expert

2. **Achievement Focus:**
   AI Infrastructure Engineer | Built 500K+ LOC Multi-Agent Platform | Open to Opportunities

3. **Value Proposition:**
   I build AI systems that work in production | Multi-Agent Orchestration | MLOps

**Character Count Guidelines:**
- Maximum: 220 characters
- Optimal: 120-150 characters
- Include: Role + Key Project + Value Prop
"""
    
    def _generate_linkedin_experience(self) -> str:
        """Generate LinkedIn experience descriptions."""
        experiences = self.profile.get('experience', [])
        
        content = "# LinkedIn Experience Descriptions\n\n"
        
        for exp in experiences:
            end_date = exp.get('end_date') or 'Present'
            bullets = "\n".join([f"• {b['text']}" for b in exp.get('bullets', [])])
            
            content += f"""
## {exp['company']}

**{exp['role']}** | {exp.get('location', 'Remote')} | {exp['start_date']} - {end_date}

### Short Description (for summary view):
{exp.get('short_description', '')}

### Full Description:
{bullets}

---
"""
        
        return content
    
    def _generate_linkedin_skills(self) -> str:
        """Generate LinkedIn skills list."""
        skills_config = self.profile.get('skills', {})
        linkedin_skills = skills_config.get('linkedin_skills', {})
        
        content = "# LinkedIn Skills\n\n"
        
        content += "## Top 3 (Pin These)\n"
        for skill in linkedin_skills.get('primary', []):
            content += f"- {skill}\n"
        
        content += "\n## Secondary Skills (Get Endorsements)\n"
        for skill in linkedin_skills.get('secondary', []):
            content += f"- {skill}\n"
        
        content += "\n## All Skills by Category\n"
        for category in skills_config.get('categories', []):
            content += f"\n### {category['name']}\n"
            for skill in category.get('skills', []):
                content += f"- {skill['name']} ({skill.get('proficiency', 'proficient')})\n"
        
        return content
    
    def _generate_linkedin_instructions(self) -> str:
        """Generate instructions for LinkedIn sync."""
        current_date = datetime.now().isoformat()
        return f"""# LinkedIn Sync Instructions

## Manual Sync Process

1. **Headline**: Copy from `headlines.md`, paste in LinkedIn profile
2. **About**: Copy from `about.md`, paste in LinkedIn About section
3. **Experience**: Update each role from `experience.md`
4. **Skills**: Reorder skills as shown in `skills.md`

## MCP-Based Sync (Automated)

If using LinkedIn MCP server:

```bash
# Using Claude Code
/linkedin sync --dry-run  # Preview changes
/linkedin sync --apply    # Apply changes
```

## Verification Checklist

- [ ] Headline updated
- [ ] About section updated
- [ ] All experience entries updated
- [ ] Skills reordered correctly
- [ ] Featured section reflects current projects
- [ ] Profile photo is professional and recent

## Last Synced

Date: {current_date}
Source: master_profile.yaml
"""
    
    # ═══════════════════════════════════════════════════════════════════════
    # GITHUB SYNC
    # ═══════════════════════════════════════════════════════════════════════
    
    def sync_github(self) -> SyncResult:
        """
        Sync master profile to GitHub profile README.
        """
        errors = []
        files_updated = []
        
        github_dir = self.root / "github" / "profile"
        github_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            readme_content = self._generate_github_readme()
            (github_dir / "README.md").write_text(readme_content)
            files_updated.append("github/profile/README.md")
            
            # Generate repo-specific READMEs
            for project in self.profile.get('projects', []):
                if project.get('pinned'):
                    repo_readme = self._generate_repo_readme(project)
                    repo_dir = github_dir.parent / "repos" / project['id']
                    repo_dir.mkdir(parents=True, exist_ok=True)
                    (repo_dir / "README.md").write_text(repo_readme)
                    files_updated.append(f"github/repos/{project['id']}/README.md")
            
        except Exception as e:
            errors.append(f"GitHub sync failed: {str(e)}")
        
        return SyncResult(
            platform=Platform.GITHUB,
            success=len(errors) == 0,
            files_updated=files_updated,
            errors=errors,
            timestamp=datetime.now()
        )
    
    def _generate_github_readme(self) -> str:
        """Generate GitHub profile README."""
        personal = self.profile['personal']
        summary = self.profile['summaries']['github']
        experiences = self.profile.get('experience', [])[:3]
        projects = [p for p in self.profile.get('projects', []) if p.get('pinned')]
        
        # Experience highlights
        exp_table = "| Company | Role | Highlight |\n|---------|------|-----------|"
        for exp in experiences:
            highlight = exp.get('bullets', [{}])[0].get('text', '')[:80] + '...' if exp.get('bullets') else ''
            exp_table += f"\n| **{exp['company']}** | {exp['role']} | {highlight} |"
        
        # Skills section
        skills = self.profile.get('skills', {}).get('categories', [])
        skills_block = ""
        for cat in skills[:4]:
            skill_names = " │ ".join([s['name'] for s in cat.get('skills', [])[:5]])
            skills_block += f"{cat['name']:12}: {skill_names}\n"
        
        # Projects section
        projects_section = ""
        for project in projects[:2]:
            highlights = "\n".join([f"- {h}" for h in project.get('highlights', [])[:4]])
            projects_section += f"""
### {project.get('name', project['id'])}
{project.get('tagline', '')}

{highlights}

[![Repo](https://img.shields.io/badge/GitHub-Repo-181717?style=flat&logo=github)]({project.get('repo_url', '#')})

"""
        
        return f"""<div align="center">

# 👋 Hi, I'm {personal['name']['full']}

**{personal['tagline']}**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-{personal['social']['linkedin'].split('/')[-1]}-0077B5?style=for-the-badge&logo=linkedin)]({personal['social']['linkedin']})
[![Email](https://img.shields.io/badge/Email-{personal['contact']['email'].replace('@', '%40')}-D14836?style=for-the-badge&logo=gmail)](mailto:{personal['contact']['email']})

</div>

---

{summary}

---

## 💼 Experience Highlights

{exp_table}

---

## 🛠️ Tech Stack

```
{skills_block}```

---

## 🏆 Featured Projects

{projects_section}

---

## 📫 Let's Connect

- 💼 Open to opportunities in **AI Infrastructure**, **Multi-Agent Systems**, or **Research Engineering**
- 🤝 Interested in collaborating on **open-source AI projects**
- 💬 Happy to chat about **multi-agent coordination**, **LLMOps**, or **production AI systems**

---

<div align="center">

*"Building AI systems that actually work in production."*

![Profile Views](https://komarev.com/ghpvc/?username={personal['social']['github'].split('/')[-1]}&color=blueviolet&style=flat-square)

</div>
"""
    
    def _generate_repo_readme(self, project: Dict) -> str:
        """Generate README for a specific repository."""
        highlights = "\n".join([f"- {h}" for h in project.get('highlights', [])])
        tech = ", ".join(project.get('technologies', []))
        
        return f"""# {project.get('name', project['id'])}

{project.get('tagline', '')}

## Overview

{project.get('description', '')}

## Highlights

{highlights}

## Tech Stack

{tech}

## Installation

```bash
# Clone the repository
git clone {project.get('repo_url', '')}
cd {project['id']}

# Install dependencies
pip install -r requirements.txt
```

## Usage

```python
# Quick start example
from {project['id']} import main

main()
```

## Documentation

See [docs/](./docs/) for full documentation.

## License

PolyForm Noncommercial 1.0.0 - see [LICENSE](./LICENSE) for details.

---

Built with ❤️ by [{self.profile['personal']['name']['full']}]({self.profile['personal']['social']['github']})
"""
    
    # ═══════════════════════════════════════════════════════════════════════
    # WEBSITE SYNC
    # ═══════════════════════════════════════════════════════════════════════
    
    def sync_website(self) -> SyncResult:
        """
        Sync master profile to website content.
        """
        errors = []
        files_updated = []
        
        try:
            from scripts.website.generator import WebsiteGenerator
            
            generator = WebsiteGenerator(
                profile_path=str(self.profile_path),
                output_dir=str(self.root / "website")
            )
            output_dir = generator.generate_all()
            files_updated.append(str(output_dir))
            
        except ImportError:
            # Fallback to basic content generation
            website_dir = self.root / "website" / "content"
            website_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate basic content files
            personal = self.profile['personal']
            
            # Homepage
            (website_dir / "index.md").write_text(f"""---
title: {personal['name']['full']}
---

# {personal['name']['full']}

{personal['headlines']['website']}

{self.profile['summaries']['website']}
""")
            files_updated.append("website/content/index.md")
            
        except Exception as e:
            errors.append(f"Website sync failed: {str(e)}")
        
        return SyncResult(
            platform=Platform.WEBSITE,
            success=len(errors) == 0,
            files_updated=files_updated,
            errors=errors,
            timestamp=datetime.now()
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # MAIN SYNC INTERFACE
    # ═══════════════════════════════════════════════════════════════════════
    
    def sync(self, platform: Platform = Platform.ALL) -> List[SyncResult]:
        """
        Sync specified platform(s) from master profile.
        
        Args:
            platform: Which platform to sync, or ALL for all platforms
            
        Returns:
            List of sync results
        """
        results = []
        
        sync_funcs = {
            Platform.RESUME: self.sync_resume,
            Platform.LINKEDIN: self.sync_linkedin,
            Platform.GITHUB: self.sync_github,
            Platform.WEBSITE: self.sync_website,
        }
        
        if platform == Platform.ALL:
            for p, func in sync_funcs.items():
                results.append(func())
        else:
            if platform in sync_funcs:
                results.append(sync_funcs[platform]())
        
        self.sync_log.extend(results)
        return results
    
    def get_sync_status(self) -> str:
        """Get formatted sync status report."""
        report = "# Platform Sync Status\n\n"
        report += f"**Profile**: {self.profile_path}\n"
        report += f"**Last Check**: {datetime.now().isoformat()}\n\n"
        
        if not self.sync_log:
            report += "*No syncs performed yet*\n"
        else:
            report += "| Platform | Status | Files Updated | Last Sync |\n"
            report += "|----------|--------|---------------|------------|\n"
            
            for result in self.sync_log[-4:]:  # Last 4 results
                status = "✅" if result.success else "❌"
                files = len(result.files_updated)
                time = result.timestamp.strftime("%Y-%m-%d %H:%M")
                report += f"| {result.platform.value} | {status} | {files} | {time} |\n"
        
        return report


def main():
    """CLI interface for sync manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync career content across platforms")
    parser.add_argument("platform", nargs="?", default="all",
                       choices=["all", "resume", "linkedin", "github", "website"],
                       help="Platform to sync")
    parser.add_argument("--status", action="store_true", help="Show sync status")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    
    args = parser.parse_args()
    
    manager = PlatformSyncManager()
    
    if args.status:
        print(manager.get_sync_status())
        return
    
    platform = Platform(args.platform)
    
    if args.dry_run:
        print(f"🔍 Dry run - would sync {platform.value}")
        print(f"Source: {manager.profile_path}")
        return
    
    print(f"🔄 Syncing {platform.value}...")
    results = manager.sync(platform)
    
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"\n{status} {result.platform.value}")
        
        if result.files_updated:
            print(f"   Files updated: {len(result.files_updated)}")
            for f in result.files_updated[:5]:
                print(f"   - {f}")
        
        if result.errors:
            print(f"   Errors:")
            for e in result.errors:
                print(f"   ⚠️ {e}")
    
    print("\n" + manager.get_sync_status())


if __name__ == "__main__":
    main()
