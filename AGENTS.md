# AGENTS.md - Multi-Agent Coordination for Career Presence

## Overview

Career Presence uses a multi-agent pattern where Claude Code orchestrates specialized tasks across job search, resume tailoring, platform management, and digital presence. This document defines the coordination protocols for complex workflows.

## Agent Roles

### 1. Discovery Agent
**Purpose**: Find and filter relevant job opportunities

**Capabilities**:
- Query JobSpy MCP for multi-platform search (LinkedIn, Indeed, Glassdoor)
- Fetch jobs from Greenhouse/Lever/Ashby APIs
- Scrape company career pages
- Initial match scoring against master profile
- Bad word penalty filtering (soft filter from `targets.yaml`)
- Experience range validation (flags under/over-qualified jobs)
- Applied-jobs deduplication via DB lookup (`tracker.filter_already_applied()`)

**Input**: Search criteria (roles, locations, companies, filters)
**Output**: List of job candidates with preliminary scores, penalties, and dedup status

**Module**: `scripts/discovery/job_searcher.py`

### 2. Analysis Agent
**Purpose**: Deep analysis of job descriptions

**Capabilities**:
- Extract requirements (must-have vs nice-to-have)
- Identify ATS keywords and phrases
- Research company context (news, culture, tech stack)
- Calculate detailed match scores against skills

**Input**: Job URL or description
**Output**: Structured JobAnalysis object with scores

**Module**: `scripts/analysis/job_analyzer.py`

### 3. Tailoring Agent
**Purpose**: Generate resume variants optimized for specific roles

**Capabilities**:
- Parse base LaTeX resume
- Apply role-specific template modifications
- Reorder experience bullets by relevance
- Optimize keywords for ATS scoring
- Compile to PDF/DOCX

**Input**: JobAnalysis + base resume + template
**Output**: Tailored resume variant (PDF)

**Module**: `scripts/tailoring/resume_tailor.py`

### 4. ATS Scoring Agent
**Purpose**: Validate resume-job match quality

**Capabilities**:
- Extract keywords from job description
- Score resume against JD requirements
- Check formatting compliance
- Identify missing keywords

**Input**: Resume PDF + Job Description
**Output**: ATS score (0-100) with recommendations

**Module**: `scripts/analysis/ats_scorer.py`

### 5. Submission Agent
**Purpose**: Automate application submission

**Capabilities**:
- Navigate application pages (Playwright MCP)
- Fill form fields intelligently
- Upload documents
- Handle multi-step applications
- Capture confirmation screenshots
- Auto-answer Easy Apply questions from `application_answers` in master profile
- DB-based deduplication check before submission (`tracker.is_already_applied()`)

**Input**: Job URL + resume + profile data
**Output**: Application confirmation

**Modules**:
- `scripts/submission/application_submitter.py`
- `scripts/submission/easy_apply_answers.py`

### 6. Tracking Agent
**Purpose**: Manage application lifecycle

**Capabilities**:
- Update application status
- Record interactions and notes
- Generate analytics and reports
- Schedule follow-ups
- Track response rates
- Deduplication queries: `is_already_applied(company, role, url)` and `filter_already_applied(jobs)`

**Input**: Application events
**Output**: Status updates, reports, dedup results

**Module**: `scripts/tracking/tracker.py`

### 7. Sync Agent
**Purpose**: Synchronize content across platforms

**Capabilities**:
- Read from master_profile.yaml
- Generate platform-specific content
- Update Resume, LinkedIn, GitHub, Website
- Ensure consistency across platforms

**Input**: master_profile.yaml changes
**Output**: Updated platform content

**Module**: `scripts/sync/sync_manager.py`

### 8. Website Agent
**Purpose**: Generate and manage personal website

**Capabilities**:
- Build Astro static site
- Generate pages from content files
- Apply site configuration
- Deploy to hosting

**Input**: Content files + site.config.ts
**Output**: Static website in `/dist`

**Module**: `scripts/website/generator.py`

### 9. LinkedIn Agent
**Purpose**: Manage LinkedIn presence and content

**Capabilities**:
- Generate profile content
- Draft and schedule posts
- Manage content calendar
- Track engagement analytics

**Input**: master_profile.yaml + content strategy
**Output**: LinkedIn content

**Module**: `scripts/linkedin/linkedin_manager.py`

### 10. Validation Agent
**Purpose**: Validate all configuration files

**Capabilities**:
- Pydantic v2 validation of `targets.yaml` and `master_profile.yaml`
- Type-safe config access via `TargetsConfig` and `MasterProfileConfig` models
- Report errors and warnings for missing or invalid configuration
- Validate `bad_words`, `experience_range`, and `application_answers` sections

**Input**: Config file paths
**Output**: Validation report with errors and warnings

**Module**: `scripts/validation/config_validator.py`
**CLI**: `cps validate`

---

## Coordination Patterns

### Sequential Pipeline (Job Application)
```
Discovery → Bad Word/Exp Filter → DB Dedup → Analysis → Tailoring → ATS Score → [Human Review] → Submission (w/ Easy Apply Answers) → Tracking
```
Standard flow for each job application.

### Parallel Discovery
```
     ┌─ JobSpy (LinkedIn) ──┐
     │                      │
Start ├─ JobSpy (Indeed) ────┼─→ Merge & Dedupe → Analysis
     │                      │
     ├─ Greenhouse API ─────┤
     │                      │
     └─ Company Careers ────┘
```
Discover from multiple sources simultaneously.

### Platform Sync
```
                    ┌─→ Resume (LaTeX)
                    │
master_profile.yaml ├─→ LinkedIn (Profile + Content)
                    │
                    ├─→ GitHub (README)
                    │
                    └─→ Website (Astro)
```
Single source of truth syncs to all platforms.

### Batch Processing
```python
for job in discovered_jobs:
    if job.match_score >= THRESHOLD:
        analysis = analyze(job)
        if analysis.score >= ATS_THRESHOLD:
            variant = tailor(job, analysis)
            queue_for_review(job, variant)
```
Process multiple jobs efficiently.

---

## Communication Protocol

### Job Discovery Request
```yaml
action: discover
params:
  query: "AI Engineer"
  locations: ["Remote", "San Francisco", "Tel Aviv"]
  platforms: ["linkedin", "indeed", "glassdoor"]
  experience_level: ["mid_senior", "senior"]
  posted_within: "24h"
  max_results: 50
```

### Job Analysis Request
```yaml
action: analyze
params:
  job_url: "https://..."
  deep_analysis: true
  research_company: true
  extract_keywords: true
```

### Resume Tailoring Request
```yaml
action: tailor
params:
  job_id: "abc123"
  template: "ai_engineer"
  include_cover_letter: false
  ats_optimize: true
```

### Platform Sync Request
```yaml
action: sync
params:
  platforms: ["resume", "linkedin", "github", "website"]
  source: "master_profile.yaml"
  dry_run: false
```

### Submission Request
```yaml
action: submit
params:
  job_id: "abc123"
  resume_path: "/path/to/variant.pdf"
  confirm: true  # ALWAYS requires explicit confirmation
```

---

## Human-in-the-Loop Checkpoints

### Required Confirmations
1. **Before first submission of the day**: Verify system state
2. **Before any submission**: Review resume variant and ATS score
3. **For Tier 1 companies**: Additional review required
4. **On any error**: Review and decide next action
5. **For non-whitelisted companies**: Manual approval needed

### Override Commands
```bash
# Skip human review for this job (use sparingly)
/apply job_123 --auto

# Force re-analysis
/analyze job_123 --force

# Cancel pending application
/cancel job_123

# Resume after CAPTCHA
/resume-automation
```

---

## Error Recovery

### On API Failure
1. Log error with full context
2. Retry with exponential backoff (3 attempts: 60s, 300s, 900s)
3. If persistent, skip and mark job for manual review
4. Notify user if critical

### On CAPTCHA Detection
1. Immediately pause all automation
2. Alert user with screenshot
3. Wait for manual resolution
4. Resume only on explicit `/resume-automation` command

### On Rate Limit
1. Log the limit hit
2. Back off according to schedule
3. Resume automatically when limit resets
4. Adjust future request timing

### On Form Mismatch
1. Screenshot the form
2. Log expected vs actual fields
3. Attempt best-effort fill
4. Flag for review if critical fields missing
5. Never submit incomplete applications

---

## Rate Limiting Coordination

Agents respect global rate limits:

```python
RATE_LIMITS = {
    # Job Discovery
    "jobspy_search": {"per_minute": 10, "per_day": 500},
    "greenhouse_api": {"per_minute": 60, "per_day": None},
    "lever_api": {"per_minute": 60, "per_day": None},

    # LinkedIn (be conservative to avoid flags)
    "linkedin_profile_view": {"per_minute": 5, "per_day": 100},
    "linkedin_job_apply": {"per_hour": 3, "per_day": 15},
    "linkedin_post": {"per_day": 1},

    # Applications
    "application_submit": {"per_hour": 5, "per_day": 20},

    # GitHub
    "github_api": {"per_hour": 5000, "per_day": None},
}
```

Before any action, agents check against shared rate limit state stored in SQLite.

---

## Configuration Management

### Personal Data Flow
```
config/master_profile.yaml (gitignored)
         ↓
    Sync Agent
         ↓
┌────────┴────────┐
│  Platform       │
│  Generators     │
└────────┬────────┘
         ↓
Generated Content (gitignored)
- website/src/config/site.config.ts
- website/src/data/pages/*.md
- linkedin/profile/content.md
- github/profile/README.md
```

### Template Files (tracked in git)
```
*.example.* files contain placeholders:
- config/master_profile.yaml.example
- website/src/config/site.config.example.ts
- website/src/data/pages/*.example.md
```

---

## Logging & Observability

All agent actions logged to `data/agent.log`:

```
[timestamp] [agent] [action] [job_id] [status] [details]
```

Example:
```
[2026-02-05T14:30:00] [discovery] [search] [*] [success] [Found 23 jobs for "AI Engineer"]
[2026-02-05T14:30:05] [analysis] [analyze] [job_123] [success] [Match: 87.5%, ATS: 82%]
[2026-02-05T14:31:00] [tailoring] [generate] [job_123] [success] [variant_anthropic_ai_20260205.pdf]
[2026-02-05T14:32:00] [ats_scorer] [score] [job_123] [success] [Score: 85/100]
[2026-02-05T14:35:00] [submission] [apply] [job_123] [success] [Confirmation captured]
[2026-02-05T14:35:01] [tracking] [update] [job_123] [success] [Status: applied]
```

---

## State Management

Application state stored in SQLite (`data/applications.db`):
- Job discovery results and metadata
- Application pipeline position
- Agent-specific state and metadata
- Retry counts and backoff state
- Rate limit tracking

Shared state prevents duplicate actions across agent invocations.

---

## Best Practices

### General
1. **Idempotency**: All actions should be safe to retry
2. **Atomicity**: Complete actions fully or rollback cleanly
3. **Visibility**: Log everything, surface errors immediately
4. **Human Agency**: Always allow override and intervention
5. **Quality over Quantity**: Better 5 great applications than 50 generic ones

### Security
1. **Never commit personal data** - Use .gitignore and .example templates
2. **Verify before commit** - Check for exposed personal info
3. **Separate configs** - Personal data in gitignored files only
4. **Credential isolation** - Store in credentials.env only

### Performance
1. **Batch operations** when possible
2. **Cache API responses** to reduce calls
3. **Parallel execution** for independent tasks
4. **Respect rate limits** proactively

### Maintainability
1. **Single source of truth** - master_profile.yaml
2. **Config-driven** - Use site.config.ts pattern
3. **Template separation** - .example files for public repo
4. **Clear module boundaries** - One agent per responsibility
