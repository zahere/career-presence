# CLAUDE.md - Career Presence System

> **Single Source of Truth**: All content flows from `config/master_profile.yaml`
> **Platforms**: Resume • LinkedIn • GitHub • Personal Website
> **Purpose**: Automated job search + professional presence management + application tracking

---

## System Overview

A comprehensive career management system that orchestrates:

1. **Multi-Platform Job Discovery** - LinkedIn, Indeed, Glassdoor, Greenhouse, Lever
2. **Deep Job Analysis** - Keyword extraction, requirement parsing, match scoring
3. **Resume Tailoring** - LaTeX-based, ATS-optimized, role-specific variants
4. **Automated Submission** - Browser automation with human-in-the-loop safety
5. **Application Tracking** - Status lifecycle, follow-ups, interview prep
6. **Digital Presence** - LinkedIn, GitHub, Website synchronization

**Core Principle**: `master_profile.yaml` is the source of truth—all platforms sync from it.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Claude Code (Career Orchestrator)                         │
│                      CLAUDE.md + Platform Agents                             │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
        ┌─────────────┬───────────┼───────────┬─────────────┐
        ▼             ▼           ▼           ▼             ▼
┌─────────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────┐
│   Resume    │ │ LinkedIn  │ │  GitHub   │ │  Website  │ │ Job Search  │
│   Engine    │ │    MCP    │ │    MCP    │ │ Generator │ │   Pipeline  │
└─────────────┘ └───────────┘ └───────────┘ └───────────┘ └─────────────┘
       │               │             │             │             │
       └───────────────┴─────────────┴─────────────┴─────────────┘
                                  │
                    ┌─────────────────────────────┐
                    │    master_profile.yaml      │
                    │    (Source of Truth)        │
                    └─────────────────────────────┘
```

### MCP Server Configuration

See `.mcp.json` for full configuration. Core servers:

| Server | Purpose | Status |
|--------|---------|--------|
| `jobspy` | Multi-platform job search (LinkedIn, Indeed, Glassdoor) | Required |
| `linkedin` | LinkedIn profile, jobs, networking | Required |
| `github` | GitHub profile and repo management | Required |
| `playwright` | Browser automation for applications | Required |
| `filesystem` | File access for resume/job data | Required |
| `fetch` | Fetch career pages and job descriptions | Required |
| `brave-search` | Company research | Optional |
| `supabase` | Cloud database for tracking | Optional |
| `slack` | Notifications | Optional |

**Setup:**
```bash
# 1. Install JobSpy MCP
git clone https://github.com/borgius/jobspy-mcp-server
cd jobspy-mcp-server && npm install && npm run build

# 2. Get LinkedIn session
uvx linkedin-scraper-mcp --get-session

# 3. Get GitHub PAT (scopes: repo, user)
# https://github.com/settings/tokens

# 4. Configure credentials
cp config/credentials.env.example config/credentials.env
# Edit with your keys
```

---

## Directory Structure

```
career-presence/
├── CLAUDE.md                         # This file - agent instructions
├── AGENTS.md                         # Multi-agent coordination
├── README.md                         # Project overview
├── pyproject.toml                    # Python dependencies (uv/pip)
├── Makefile                          # Development commands
├── .mcp.json                         # MCP server configuration
│
├── config/
│   ├── master_profile.yaml           # ⭐ SINGLE SOURCE OF TRUTH
│   ├── targets.yaml                  # Target companies, whitelist
│   ├── credentials.env               # API keys (gitignored)
│   └── credentials.env.example       # Template for credentials
│
├── data/
│   ├── experiences.json              # Structured experience bullets
│   ├── skills.json                   # Skills with proficiency levels
│   ├── projects.json                 # Project descriptions
│   └── applications.db               # SQLite tracking (gitignored)
│
├── resume/
│   ├── base/master.tex               # Master LaTeX resume (READ-ONLY)
│   ├── sections/                     # Modular resume sections
│   ├── templates/                    # Role-specific templates
│   │   ├── ai_engineer.tex
│   │   ├── platform_engineer.tex
│   │   ├── research_engineer.tex
│   │   └── founding_engineer.tex
│   ├── variants/                     # Generated variants (gitignored)
│   └── exports/                      # PDF/DOCX outputs (gitignored)
│
├── linkedin/
│   ├── profile/
│   │   └── content.md                # Generated profile content
│   ├── posts/
│   │   ├── drafts/
│   │   ├── scheduled/
│   │   └── published/
│   └── analytics/
│
├── github/
│   ├── profile/
│   │   └── README.md                 # Profile README
│   └── repos/
│       └── agenticraft/              # Flagship project docs
│
├── portfolio/
│   ├── website/
│   │   └── src/pages/                # Website source
│   └── github/
│       └── README.md                 # Alternative README
│
├── jobs/
│   ├── discovered/                   # Raw job data (gitignored)
│   ├── analyzed/                     # Processed with scores (gitignored)
│   └── applied/                      # Submission records (gitignored)
│
├── interviews/
│   ├── prep/                         # Company-specific prep
│   ├── stories/                      # STAR stories
│   └── questions/                    # Technical questions
│
├── scripts/
│   ├── __init__.py
│   ├── cli.py
│   ├── analysis/
│   │   ├── ats_scorer.py
│   │   └── job_analyzer.py
│   ├── discovery/
│   │   └── job_searcher.py          # renamed from search_jobs.py
│   ├── linkedin/
│   │   └── linkedin_manager.py      # renamed + merged from content_manager.py
│   ├── submission/
│   │   └── application_submitter.py
│   ├── sync/
│   │   └── sync_manager.py          # renamed from platform_sync.py
│   ├── tailoring/
│   │   └── resume_tailor.py
│   ├── tracking/
│   │   └── tracker.py
│   └── website/
│       └── generator.py
│
├── templates/
│   ├── cover_letters/
│   └── responses/                    # Email response templates
│
├── materials/                        # Supporting documentation
│   └── agenticraft_overview.md
│
├── tests/                            # Test suite
│   └── test_ats_scorer.py
│
└── docs/                             # Reference documents
    ├── PROJECT_PLAN.md
    ├── QUICK_REFERENCE.md
    ├── SYNTHESIS_RECOMMENDATIONS.md
    └── DIGITAL_PRESENCE_EXPANSION.md
```

---

## Critical Rules

### 🚨 NEVER MODIFY
- `resume/base/master.tex` - Always copy, never edit directly
- `config/credentials.env` - Read-only access

### Security & Privacy
- ❌ Never expose credentials in logs
- ❌ Never commit credentials to git
- ❌ Never commit personal/sensitive data (names, emails, phone numbers, addresses)
- ❌ Never expose real profile content (master_profile.yaml, linkedin/profile/, github/profile/)
- ✅ Store credentials in `credentials.env` (gitignored)
- ✅ Use `.example` templates for public repo (with placeholder data)
- ✅ Redact personal info in error messages
- ✅ Always verify .gitignore covers sensitive files before committing
- ✅ Use separate browser profile for automation

**Gitignored Personal Data:**
- `config/master_profile.yaml` → use `master_profile.yaml.example`
- `linkedin/profile/` → generated LinkedIn content
- `github/profile/README.md` → personal GitHub profile
- `resume/base/master.tex` → personal resume content
- `data/experiences.json`, `data/projects.json`, `data/skills.json` → personal data

---

## Master Profile Structure

All platforms sync from `config/master_profile.yaml`:

```yaml
personal:
  name: "Your Name"
  email: "you@example.com"
  phone: "+1-555-000-0000"
  location: "City, Country"
  linkedin: "linkedin.com/in/yourprofile"
  github: "github.com/yourusername"
  website: "yourwebsite.dev"

headlines:
  primary: "Your Role | Your Specialty"
  linkedin: "Building [Project] | Your Role | Your Expertise"
  github: "Your Role specializing in [Your Specialty]"

bios:
  short_50: "Your role in brief..."
  medium_150: "Your professional summary with key expertise..."
  long_300: "..."
  linkedin_2600: "..."

talking_points:
  - "Key achievement with metrics"
  - "Another achievement with impact"
  - "Technical accomplishment"

skills:
  languages: [Python, TypeScript, Go, Rust]
  ml_frameworks: [PyTorch, LangChain, LlamaIndex, Transformers]
  infrastructure: [Kubernetes, Docker, Terraform, AWS, GCP]
  databases: [PostgreSQL, Redis, Pinecone, Weaviate]

preferences:
  remote: true
  locations: ["City", "Remote", "Country"]
  salary_min: 100000
  visa_required: false

target_roles:
  - "Role 1"
  - "Role 2"
  - "Role 3"

target_companies:
  tier1: ["Anthropic", "OpenAI", "Google DeepMind", "Meta AI"]
  tier2: ["Databricks", "Scale AI", "Cohere", "Hugging Face"]
  tier3: ["AI startups with >$10M funding"]
```

---

## Job Search Pipeline

### Phase 1: Discovery

#### Multi-Platform Search
```yaml
action: discover
platforms: [linkedin, indeed, glassdoor]
params:
  keywords: ["AI Engineer", "ML Engineer", "LLM Engineer", "MLOps Engineer"]
  locations: ["Remote", "Tel Aviv", "San Francisco, CA"]
  experience_level: ["mid_senior", "senior", "lead"]
  posted_within: "24h"
  max_results: 50
```

#### Company Career Pages
- Greenhouse API: `boards-api.greenhouse.io/v1/boards/{token}/jobs`
- Lever API: `api.lever.co/v0/postings/{company}`
- Ashby API: `api.ashbyhq.com/posting-api/job-board/{company}`

#### Deduplication
Match by: `job_url` OR `(company + role + location)`

### Phase 2: Job Evaluation

#### Match Score Calculation (0-100)
```python
def calculate_match_score(job, profile):
    score = 0

    # Keyword Overlap (40 points)
    job_keywords = extract_keywords(job.description)
    profile_keywords = profile.all_skills
    overlap = len(set(job_keywords) & set(profile_keywords)) / len(job_keywords)
    score += overlap * 40

    # Experience Level Match (30 points)
    if job.experience_level in profile.target_levels:
        score += 30
    elif is_adjacent_level(job.experience_level, profile.target_levels):
        score += 15

    # Location/Remote Match (20 points)
    if job.is_remote and profile.prefers_remote:
        score += 20
    elif job.location in profile.preferred_locations:
        score += 20

    # Company Type Fit (10 points)
    if job.company_type in profile.preferred_company_types:
        score += 10

    return score
```

#### Threshold Actions
| Score | Action |
|-------|--------|
| **≥ 70** | Proceed to tailoring |
| **60-69** | Flag for manual review |
| **< 60** | Skip (log for analytics) |

### Phase 3: Resume Tailoring

#### Template Selection
| Job Signals | Template | Lead With |
|-------------|----------|-----------|
| "multi-agent", "LLM", "AI infrastructure" | `ai_engineer.tex` | AgentiCraft |
| "Kubernetes", "DevOps", "platform" | `platform_engineer.tex` | Infrastructure |
| "research", "papers", "experiments" | `research_engineer.tex` | Academic rigor |
| "startup", "founding", "0-to-1" | `founding_engineer.tex` | Entrepreneurial |

#### Tailoring Strategy

**Professional Summary Pattern:**
```latex
% [Role-relevant intro] + [Key achievement with metric] + [Platform/scale expertise]
AI Infrastructure Engineer specializing in [KEYWORD: multi-agent systems]
with expertise in [KEYWORD: LLMOps at scale]. Built AgentiCraft platform
serving 100+ concurrent agents with <150ms latency.
```

**Experience Bullets:**
- Reorder bullets to front-load JD-relevant achievements
- Mirror exact JD phrases where truthful
- Lead with: action verb → context → impact → metric
- Bad: "Worked on ML pipeline"
- Good: "Architected MLOps pipeline reducing deployment time from 2 hours to <2 minutes"

**Skills Section:**
- Reorder to match JD priority (most relevant first)
- Group by JD categories if present
- Include exact matches for ATS keyword scanning

#### Keyword Rules
✅ **DO**: Mirror exact JD phrases, add keywords naturally, use recognized synonyms
❌ **DON'T**: Change metrics, fabricate experience, keyword-stuff unnaturally

#### LaTeX Compilation
```bash
pdflatex -interaction=nonstopmode variant.tex  # Run twice for cross-refs
```

### Phase 4: ATS Scoring (Target: 80%+)

```python
def calculate_ats_score(resume_text, job_description):
    score = 0

    # 1. Keyword Match (40 points)
    job_keywords = extract_technical_keywords(job_description)
    resume_keywords = extract_technical_keywords(resume_text)
    overlap = len(set(job_keywords) & set(resume_keywords)) / len(job_keywords)
    score += overlap * 40

    # 2. Section Presence (20 points)
    required_sections = ['Experience', 'Education', 'Technical Skills', 'Projects']
    sections_present = sum(s.lower() in resume_text.lower() for s in required_sections)
    score += (sections_present / len(required_sections)) * 20

    # 3. Quantifiable Metrics (20 points)
    metrics = re.findall(r'\d+[%x]|\$[\d,]+|\d+\+?\s*(?:years?|yrs?)', resume_text)
    score += min(len(metrics) / 10, 1.0) * 20

    # 4. Formatting Quality (20 points)
    if is_text_extractable(resume_text): score += 10
    if has_standard_fonts(resume_text): score += 5
    if is_single_column(resume_text): score += 5

    return int(score)
```

#### ATS Checklist
- [ ] Standard headers: Experience, Education, Skills, Projects
- [ ] No tables, text boxes, or graphics
- [ ] Single-column layout
- [ ] 10-12pt standard font (Roboto, Arial, Calibri)
- [ ] PDF format (unless DOCX required)
- [ ] Include 60-80% of JD keywords naturally
- [ ] Dates in consistent format: MMM YYYY or YYYY

#### Review Gates
| ATS Score | Action |
|-----------|--------|
| **≥ 85%** | Auto-apply if company whitelisted |
| **80-84%** | Ready to apply, await confirmation |
| **70-79%** | Needs review, send notification |
| **< 70%** | Reject variant, regenerate |

### Phase 5: Application Submission

#### Whitelist Companies
```yaml
tier1:  # Auto-apply enabled
  - Anthropic
  - OpenAI
  - Google DeepMind
  - Meta AI

tier2:  # Auto-apply enabled
  - Databricks
  - Scale AI
  - Cohere
  - Hugging Face
  - Weights & Biases

tier3:  # Requires confirmation
  - Vercel
  - Supabase
  - Modal
  - Anyscale
```

#### Safety Checks (Before Any Submission)
1. ✅ Resume variant exists and is valid PDF
2. ✅ ATS score ≥ 80%
3. ✅ Match score ≥ 70%
4. ✅ Not already applied to this role
5. ✅ Company not in exclusion list
6. ✅ Human confirmation received (unless whitelisted + ATS ≥ 85%)

#### Human Confirmation Required For
- Non-whitelisted companies
- ATS score < 85%
- Jobs with custom questions
- First application of the day (sanity check)

### Phase 6: Tracking & Follow-up

#### Status Lifecycle
```
discovered → analyzing → ready → applied → responded → interviewing → offer/rejected
                                    │
                                    └── follow_up (after 7 days)
```

#### Interview Preparation (When status → interviewing)
1. Research company recent news
2. Generate expected interview questions
3. Prepare STAR stories from resume bullets
4. Send prep document

#### Follow-up (7 days after application, no response)
1. Generate follow-up email draft
2. Suggest LinkedIn connection to hiring manager
3. Update status to 'follow_up_pending'

---

## Platform-Specific Management

### 📄 RESUME

#### Commands
```
/resume status              # Show variants and sync status
/resume generate [job_id]   # Generate tailored variant
/resume export [format]     # Export to PDF/DOCX
/resume sync                # Sync from master_profile.yaml
```

### 💼 LINKEDIN

#### Commands
```
/linkedin status            # Profile completeness score
/linkedin optimize          # Suggest profile improvements
/linkedin sync              # Sync from master_profile.yaml
/linkedin post [type]       # Draft new post
/linkedin schedule          # View/manage content calendar
/linkedin analytics         # View engagement metrics
/linkedin headline [job_id] # Suggest headline for job
/linkedin connect [name] [company] [context]  # Generate connection request
```

#### Profile Optimization Checklist
- [ ] **Headline** (220 chars): Role + Value Prop + Keywords
- [ ] **About** (2600 chars): Hook + Story + Skills + CTA
- [ ] **Experience**: Metrics-driven, keyword-rich bullets
- [ ] **Featured**: AgentiCraft, top project, recent post
- [ ] **Skills**: Top 3 pinned, 50 total for endorsements
- [ ] **Recommendations**: 3+ colleagues

#### Headline Formula
```
[Current Role] | [Key Skill/Project] | [Value Proposition]
Example: "Building AgentiCraft | AI Infrastructure Engineer | Multi-Agent Systems"
```

#### Content Calendar
| Day | Content Type |
|-----|-------------|
| Mon | Technical Insight |
| Wed | Project Update |
| Fri | Industry Commentary |

### 🐙 GITHUB

#### Commands
```
/github status              # Profile and repo overview
/github readme update       # Update profile README
/github repo optimize [repo]# Optimize repo presentation
/github sync                # Sync from master_profile.yaml
/github topics [repo]       # Suggest topics for repo
```

#### Profile README Structure
```markdown
## 👋 Hi, I'm [Name]
**[Tagline]**

### 🚀 Current Focus
- Building **[Main Project]** - [Description]

### 💼 Experience Highlights
- **[Company]** - [Key achievement with metric]

### 🛠️ Tech Stack
[Category]: [Skills]

### 📫 Connect
- LinkedIn: [link]
- Email: [email]
```

#### Repository Optimization
1. **Description**: Clear, keyword-rich (350 chars)
2. **README**: Problem → Solution → Demo → Install → Usage
3. **Topics**: 5-10 relevant tags
4. **License**: PolyForm Noncommercial 1.0.0 (or MIT/Apache for open source)
5. **Social Preview**: Custom image

### 🌐 WEBSITE

#### Commands
```
/website status             # Build status and deploy info
/website build              # Generate static site
/website deploy             # Deploy to hosting
/website blog new [title]   # Create new blog post
/website sync               # Sync from master_profile.yaml
```

#### Sections
1. Hero - Name, tagline, CTAs
2. About - Professional summary
3. Projects - Featured work with demos
4. Experience - Timeline view
5. Skills - Visual grid
6. Blog - Technical writing
7. Contact - Form + social links

---

## Workflow Commands

### Job Search
```
/discover [criteria]        # Search for jobs
/analyze [job_url]          # Deep analysis
/tailor [job_id]            # Generate resume variant
/apply [job_id] --confirm   # Submit application
/status                     # Pipeline summary
/track [app_id] [action]    # Update application status
```

### Sync
```
/sync all                   # Sync all platforms
/sync [platform]            # Sync specific platform
/sync pull [platform]       # Pull updates to master
```

### Presence
```
/prepare [job_id]           # Prepare ALL platforms for application
/presence report            # Full digital presence audit
/presence gaps              # Identify weak areas
/presence metrics           # Show engagement metrics
```

### Maintenance
```
/resume-automation          # Resume after CAPTCHA/pause
/regenerate [job_id]        # Regenerate failed variant
/export csv                 # Export applications to CSV
```

---

## Schedules

### Daily
- **Morning**: Check job discoveries, review pending applications
- **Midday**: LinkedIn engagement (comment on 3-5 posts)
- **Evening**: Draft content for scheduled posts

### Weekly
| Day | Focus |
|-----|-------|
| Mon | Job discovery + application review |
| Tue | LinkedIn content creation |
| Wed | GitHub maintenance |
| Thu | Resume variant generation |
| Fri | Analytics review + strategy |
| Sat | Blog writing |
| Sun | Planning + sync check |

### Daily Summary (6 PM)
```
╔════════════════════════════════════════════════════════════════╗
║                    DAILY APPLICATION SUMMARY                    ║
╠════════════════════════════════════════════════════════════════╣
║  Jobs Scraped Today:     47                                     ║
║  Resumes Generated:      12                                     ║
║  Applications Submitted:  5                                     ║
║  Avg ATS Score:          84%                                    ║
╠════════════════════════════════════════════════════════════════╣
║  TOP OPPORTUNITIES:                                             ║
║  1. AI Engineer @ Anthropic (Match: 92%)                       ║
║  2. ML Platform @ Databricks (Match: 88%)                      ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Rate Limiting

| Platform | Limit | Notes |
|----------|-------|-------|
| LinkedIn (MCP) | 5/min, 100/day | Avoid account flags |
| JobSpy | 10/min | Respect API limits |
| Greenhouse API | Unlimited | Public API |
| GitHub API | 5000/hour | With PAT |
| Applications | 5/hour, 20/day | Quality > quantity |
| Post publishing | 1/day max | Avoid spam flags |

### Backoff Strategy
```python
BACKOFF_SCHEDULE = [60, 300, 900, 3600]  # seconds

def with_retry(func, max_attempts=4):
    for attempt in range(max_attempts):
        try:
            return func()
        except RateLimitError:
            if attempt < max_attempts - 1:
                wait = BACKOFF_SCHEDULE[attempt]
                log(f"Rate limited, waiting {wait}s")
                sleep(wait)
            else:
                raise
```

---

## Error Handling

| Error | Action |
|-------|--------|
| JobSpy fails | Retry 3x with backoff, then skip platform |
| LaTeX compilation fails | Log error, mark 'failed', notify |
| LinkedIn auth fails | **PAUSE ALL**, notify immediately |
| Playwright form error | Screenshot, log, retry once, skip |
| CAPTCHA detected | Pause, alert human, wait for `/resume-automation` |
| Database unreachable | Queue operations, retry every 5 min |
| GitHub PAT expired | Generate new token with repo, user scopes |

### Error Message Templates
```
⚠️ CAPTCHA detected on {platform}
Action: Pausing automation. Please solve manually.
Resume with: /resume-automation

⚠️ Rate limit hit on {platform}
Action: Backing off for {duration}
Auto-resume at: {timestamp}

❌ Form submission failed: {error}
Screenshot saved: jobs/applied/{job_id}/error.png
Action: Review and retry with /apply {job_id} --retry
```

---

## Success Metrics

### LinkedIn
- Profile views: 100+/week
- Post impressions: 1000+/post
- Connection requests: 10+/week
- SSI Score: 70+

### GitHub
- Profile views: Track via insights
- Repo stars: Track growth
- Contribution graph: Consistent activity

### Job Search
- Applications sent: Track weekly
- Response rate: Target 15%+
- Interview rate: Target 10%+

---

## Logging

All actions logged to `data/agent.log`:
```
[2025-02-04 14:30:00] INFO: Discovered 15 new jobs matching criteria
[2025-02-04 14:30:05] INFO: Analyzing job_abc123 at Company XYZ
[2025-02-04 14:31:00] INFO: Generated variant resume_xyz_ai_engineer_20250204
[2025-02-04 14:35:00] INFO: Submitted application (screenshot: app_xyz_confirm.png)
```

---

## Python Environment

### Setup with uv (Recommended)
```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install dependencies
make install-dev

# Or manually:
uv venv
uv pip install -e ".[dev]"

# Activate
source .venv/bin/activate

# Install Playwright browsers
uv run playwright install chromium
```

### Installation Options
```bash
make install       # Core dependencies
make install-dev   # Core + dev tools (pytest, ruff, mypy)
make install-ai    # Core + AI/LLM (openai, anthropic, langchain)
make install-all   # Everything
```

### CLI Usage
```bash
uv run cps --help           # Show all commands
uv run cps status           # Pipeline status
uv run cps discover "AI Engineer remote"
uv run cps ats-score resume/exports/resume.pdf
```

---

## Getting Started

```bash
# 1. Setup Python environment
make install-dev
source .venv/bin/activate

# 2. Configure credentials
cp config/credentials.env.example config/credentials.env
# Edit with your API keys

# 3. Initialize master profile
# Edit config/master_profile.yaml with your information

# 4. Setup MCP servers (see .mcp.json)
# Install JobSpy, get LinkedIn session, etc.

# 5. Sync all platforms
/sync all

# 6. Review each platform
/resume status
/linkedin status
/github status
/website status

# 7. Start job search
/discover AI Engineer remote
```

---

## Quick Reference

```
# Job Search Pipeline
/discover → /analyze → /tailor → /apply → /track

# Platform Management
/resume status|generate|export|sync
/linkedin status|optimize|sync|post|schedule|analytics
/github status|readme|repo|sync|topics
/website status|build|deploy|blog|sync

# Sync Operations
/sync all|[platform]|pull [platform]

# Presence
/prepare [job_id]
/presence report|gaps|metrics
```