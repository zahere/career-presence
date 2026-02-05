# Career Presence System - Quick Reference

## What This System Does

Manages your entire professional presence from a single source of truth:

```
config/master_profile.yaml
       |
       |--- Resume (LaTeX, ATS-optimized, role-tailored)
       |--- LinkedIn (Profile, Posts, Content Strategy)
       |--- GitHub (Profile README, Repo Showcases)
       |--- Website (Astro portfolio, Blog, Contact)
       |--- Job Search (Discover, Analyze, Tailor, Apply, Track)
```

## Project Structure

```
career-presence/
├── config/
│   ├── master_profile.yaml       # Single source of truth
│   ├── master_profile.yaml.example
│   ├── targets.yaml              # Target companies, bad words, experience range
│   ├── credentials.env           # API keys (gitignored)
│   └── credentials.env.example
├── scripts/
│   ├── cli.py                    # CLI entry point (uv run cps)
│   ├── analysis/
│   │   ├── ats_scorer.py         # ATS compatibility scoring
│   │   └── job_analyzer.py       # Job description analysis + match scoring
│   ├── discovery/
│   │   └── job_searcher.py       # Multi-platform search, bad word filter, dedup
│   ├── submission/
│   │   ├── application_submitter.py  # Playwright-based form submission
│   │   └── easy_apply_answers.py     # Auto-answer common application questions
│   ├── tailoring/
│   │   └── resume_tailor.py      # Role-specific resume variant generation
│   ├── tracking/
│   │   └── tracker.py            # SQLite application tracking + analytics
│   ├── sync/
│   │   └── sync_manager.py       # Cross-platform sync from master profile
│   ├── validation/
│   │   └── config_validator.py   # Pydantic-based config validation
│   ├── linkedin/
│   │   └── linkedin_manager.py   # Content strategy + post management
│   └── website/
│       └── generator.py          # Astro portfolio site generator
├── resume/
│   ├── base/master.tex           # Master LaTeX resume (READ-ONLY)
│   ├── templates/                # Role-specific templates
│   ├── variants/                 # Generated variants (gitignored)
│   └── exports/                  # PDF/DOCX outputs (gitignored)
├── data/
│   └── applications.db           # SQLite tracking database (gitignored)
├── tests/                        # Test suite (118 tests)
├── website/                      # Astro portfolio site
├── CLAUDE.md                     # Agent instructions
└── AGENTS.md                     # Multi-agent coordination
```

## Setup

```bash
# 1. Install Python dependencies
make install-dev          # or: uv pip install -e ".[dev]"
source .venv/bin/activate

# 2. Configure credentials
cp config/credentials.env.example config/credentials.env
# Edit with your API keys

# 3. Set up master profile
# Edit config/master_profile.yaml with your information

# 4. Validate configuration
uv run cps validate

# 5. Install Playwright browsers (for application submission)
uv run playwright install chromium
```

## CLI Commands

All commands use `uv run cps <command>`.

### Job Search Pipeline

```bash
# Discover jobs
uv run cps discover "AI Engineer remote"
uv run cps discover "ML Engineer" --platforms linkedin,indeed --limit 50
uv run cps discover "Platform Engineer" --location "San Francisco" --hours 24
uv run cps discover "AI Engineer" --locale israel    # Region-specific config

# Analyze a job posting
uv run cps analyze https://boards.greenhouse.io/company/jobs/12345
uv run cps analyze https://lever.co/company/12345 --deep

# Generate tailored resume
uv run cps tailor job_12345
uv run cps tailor job_12345 --template ai_engineer

# Score resume for ATS compatibility
uv run cps ats-score resume/exports/resume.pdf --job-text "Job description here"
uv run cps ats-score resume.pdf --job-path jobs/analyzed/description.txt

# Submit application
uv run cps apply job_12345 --confirm
uv run cps apply job_12345 --auto          # Auto-apply (whitelisted companies only)
```

### Application Tracking

```bash
# View pipeline status
uv run cps status

# Update application status
uv run cps track app_12345 response "Got email from recruiter"
uv run cps track app_12345 interview "Phone screen scheduled"
uv run cps track app_12345 offer "Received offer"
uv run cps track app_12345 rejected
uv run cps track app_12345 withdrawn "Accepted other offer"
```

### Platform Sync

```bash
uv run cps sync              # Sync all platforms
uv run cps sync resume       # Sync resume only
uv run cps sync linkedin     # Sync LinkedIn only
uv run cps sync github       # Sync GitHub only
uv run cps sync website      # Sync website only
uv run cps sync --dry-run    # Preview changes without applying
```

### Presence Management

```bash
uv run cps prepare job_12345   # Prepare all platforms for a specific application
uv run cps presence report     # Full digital presence audit
uv run cps presence gaps       # Identify weak areas
uv run cps presence metrics    # Show engagement metrics
```

### Configuration

```bash
uv run cps validate            # Validate targets.yaml + master_profile.yaml
```

## Pipeline Flow

```
discover --> analyze --> tailor --> ats-score --> apply --> track
   |            |           |          |            |         |
   |  Match     | Keywords  | LaTeX    | Score     | Submit  | Status
   |  Score     | Must-have | variant  | >= 80%?   | + dedup | lifecycle
   |  >= 70%    | Nice-have | per role |           | check   |
   v            v           v          v           v         v
 Filter by   Extract     Select     Keyword    Safety     discovered
 bad words,  require-    template:  match 40%  checks:    --> analyzing
 exp range,  ments,      ai_eng,   sections   ATS>=80    --> ready
 exclusions  skills      platform,  20%        match>=70  --> applied
             match       research,  metrics    not dup    --> responded
                         founding   20%        confirm    --> interviewing
                                    format 20%            --> offer/rejected
```

## Configuration Files

### config/targets.yaml

Defines target companies, bad words, and experience range:

```yaml
tiers:
  tier1: [Anthropic, OpenAI, Google DeepMind]      # Auto-apply enabled
  tier2: [Databricks, Scale AI, Cohere]             # Auto-apply enabled
  tier3: [Vercel, Supabase, Modal]                  # Requires confirmation

target_roles:
  - "AI Engineer"
  - "ML Engineer"
  - "Platform Engineer"

bad_words:                          # Soft penalty (not hard exclude)
  title_words: [intern, junior]     # Penalty per match in title
  description_words: [unpaid]       # Penalty per match in description
  penalty_per_match: 5              # Points deducted per match

experience_range:                   # Flag jobs outside range
  min_years: 3
  max_years: 10

exclusions:                         # Hard exclude
  companies: ["Company X"]
  keywords: ["security clearance"]

locales:                            # Region-specific overrides
  israel:
    tiers: { tier1: [Mobileye, Check Point] }
    locations: ["Tel Aviv", "Haifa"]
```

### config/master_profile.yaml

Source of truth for all platforms. Key sections:

- `personal` - Name, contact, social links
- `headlines` - Platform-specific headlines
- `summaries` - Bio variants by platform
- `experience` - Work history with bullets
- `skills` - Categorized skills with proficiency
- `projects` - Featured projects
- `education` - Academic background
- `application_answers` - Auto-fill for Easy Apply questions

## ATS Score Breakdown

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| Keyword Match | 40% | JD keywords found in resume |
| Section Presence | 20% | Experience, Education, Skills, Projects, Summary |
| Quantifiable Metrics | 20% | Numbers, percentages, dollar amounts |
| Formatting Quality | 20% | Text extractability, structure, encoding |

| Score | Recommendation |
|-------|----------------|
| 85+ | Auto-apply (whitelisted companies) |
| 80-84 | Ready to apply |
| 70-79 | Needs review |
| < 70 | Regenerate variant |

## Application Safety Checks

Before any submission:

1. Resume variant exists and is valid PDF
2. ATS score >= 80%
3. Match score >= 70%
4. Not already applied (database dedup by URL, company+role)
5. Company not in exclusion list
6. Human confirmation (unless whitelisted + ATS >= 85%)

## Resume Templates

| Job Signals | Template | Lead With |
|-------------|----------|-----------|
| "multi-agent", "LLM", "AI infrastructure" | `ai_engineer.tex` | AgentiCraft |
| "Kubernetes", "DevOps", "platform" | `platform_engineer.tex` | Infrastructure |
| "research", "papers", "experiments" | `research_engineer.tex` | Academic rigor |
| "startup", "founding", "0-to-1" | `founding_engineer.tex` | Entrepreneurial |

## Status Lifecycle

```
discovered --> analyzing --> ready --> applied --> responded --> interviewing --> offer
                                         |                                      |
                                         +-- follow_up (7 days, no response)    rejected
                                         |
                                         withdrawn
```

## Rate Limits

| Platform | Limit |
|----------|-------|
| LinkedIn MCP | 5/min, 100/day |
| JobSpy | 10/min |
| GitHub API | 5000/hour |
| Applications | 5/hour, 20/day |
| Posts | 1/day max |

## MCP Servers

| Server | Purpose | Required |
|--------|---------|----------|
| `jobspy` | Multi-platform job search | Yes |
| `playwright` | Browser automation for applications | Yes |
| `github` | GitHub profile and repo management | Yes |
| `filesystem` | File access for resume/job data | Yes |
| `context7` | Up-to-date library documentation | No |

See `.mcp.json` for full configuration.

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check scripts/

# Format
uv run ruff format scripts/

# Type check
uv run python -m mypy scripts/ --ignore-missing-imports

# All checks
uv run ruff check scripts/ && uv run pytest tests/ -v
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| LinkedIn auth expired | `uvx linkedin-scraper-mcp --get-session` |
| GitHub PAT expired | Generate new at github.com/settings/tokens (scopes: repo, user) |
| LaTeX compile error | Verify `pdflatex` installed: `which pdflatex` |
| Playwright not working | `uv run playwright install chromium` |
| Config validation fails | `uv run cps validate` for detailed errors |
| Database locked | Check for stale processes: `lsof data/applications.db` |

---

**Remember**: Quality > Quantity. 5 tailored applications beat 50 generic ones.
