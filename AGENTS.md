# AGENTS.md - Multi-Agent Coordination for AutoApply

## Overview

AutoApply uses a multi-agent pattern where Claude Code orchestrates specialized tasks.
This document defines the coordination protocols for complex workflows.

## Agent Roles

### 1. Discovery Agent
**Purpose**: Find and filter relevant job opportunities

**Capabilities**:
- Query LinkedIn MCP for job listings
- Fetch jobs from Greenhouse/Lever APIs
- Scrape company career pages
- Initial match scoring

**Input**: Search criteria (roles, locations, companies)
**Output**: List of job candidates with preliminary scores

### 2. Analysis Agent
**Purpose**: Deep analysis of job descriptions

**Capabilities**:
- Extract requirements (must-have vs nice-to-have)
- Identify ATS keywords
- Research company context
- Calculate detailed match scores

**Input**: Job URL or description
**Output**: Structured JobAnalysis object

### 3. Tailoring Agent
**Purpose**: Generate resume variants

**Capabilities**:
- Parse base LaTeX resume
- Apply role-specific modifications
- Optimize for ATS
- Compile to PDF/DOCX

**Input**: JobAnalysis + base resume
**Output**: Tailored resume variant

### 4. Submission Agent
**Purpose**: Automate application submission

**Capabilities**:
- Navigate application pages (Playwright)
- Fill form fields
- Upload documents
- Capture confirmation

**Input**: Job URL + resume + profile data
**Output**: Application confirmation

### 5. Tracking Agent
**Purpose**: Manage application lifecycle

**Capabilities**:
- Update application status
- Record interactions
- Generate analytics
- Schedule follow-ups

**Input**: Application events
**Output**: Status updates, reports

## Coordination Patterns

### Sequential Pipeline
```
Discovery → Analysis → Tailoring → [Human Review] → Submission → Tracking
```

Standard flow for each application.

### Parallel Discovery
```
     ┌─ LinkedIn MCP ──┐
     │                 │
Start ├─ Greenhouse API ─┼─→ Merge & Dedupe → Analysis
     │                 │
     └─ Company Sites ─┘
```

Discover from multiple sources simultaneously.

### Batch Processing
```
For each job in discovered_jobs:
  if match_score > threshold:
    analyze(job)
    tailor(job)
    queue_for_review(job)
```

Process multiple jobs in batch.

## Communication Protocol

### Job Discovery Request
```yaml
action: discover
params:
  query: "AI Engineer"
  locations: ["Remote", "San Francisco"]
  companies: ["tier1", "tier2"]
  max_results: 50
```

### Job Analysis Request
```yaml
action: analyze
params:
  job_url: "https://..."
  deep_analysis: true
  research_company: true
```

### Tailoring Request
```yaml
action: tailor
params:
  job_id: "abc123"
  variant_type: "ai_engineer"
  include_cover_letter: true
```

### Submission Request
```yaml
action: submit
params:
  job_id: "abc123"
  resume_path: "/path/to/variant.pdf"
  confirm: true  # Requires explicit confirmation
```

## Human-in-the-Loop Checkpoints

### Required Confirmations
1. **Before first submission of the day**: Verify system state
2. **Before any submission**: Review resume variant
3. **For high-stakes applications**: Tier 1 companies
4. **On any error**: Review and decide next action

### Override Commands
```bash
# Skip human review for this job
/apply job_123 --auto

# Force re-analysis
/analyze job_123 --force

# Cancel pending application
/cancel job_123
```

## Error Recovery

### On API Failure
1. Log error with context
2. Retry with exponential backoff (3 attempts)
3. If persistent, skip and mark job for manual review

### On CAPTCHA
1. Pause automation
2. Alert user
3. Wait for manual resolution
4. Resume on `/resume` command

### On Form Mismatch
1. Screenshot the form
2. Log expected vs actual fields
3. Attempt best-effort fill
4. Flag for review if critical fields missing

## Rate Limiting Coordination

Agents respect global rate limits:

```python
RATE_LIMITS = {
    "linkedin_profile_view": {"per_minute": 5, "per_day": 100},
    "linkedin_job_search": {"per_minute": 10, "per_day": 500},
    "greenhouse_api": {"per_minute": 60, "per_day": None},
    "application_submit": {"per_hour": 5, "per_day": 20},
}
```

Before any action, agents check against shared rate limit state.

## Logging & Observability

All agent actions logged to `data/agent.log`:

```
[timestamp] [agent] [action] [job_id] [status] [details]
```

Example:
```
[2025-02-04T14:30:00] [discovery] [search] [*] [success] [Found 23 jobs for "AI Engineer"]
[2025-02-04T14:30:05] [analysis] [analyze] [job_123] [success] [Match score: 87.5%]
[2025-02-04T14:31:00] [tailoring] [generate] [job_123] [success] [Created variant_anthropic_ai_20250204]
[2025-02-04T14:35:00] [submission] [apply] [job_123] [success] [Confirmation captured]
```

## State Management

Application state stored in SQLite:
- Current pipeline position for each job
- Agent-specific metadata
- Retry counts and backoff state

Shared state prevents duplicate actions across agent invocations.

## Best Practices

1. **Idempotency**: All actions should be safe to retry
2. **Atomicity**: Complete actions fully or rollback
3. **Visibility**: Log everything, surface errors
4. **Human Agency**: Always allow override and intervention
5. **Quality over Quantity**: Better 5 great applications than 50 generic ones
