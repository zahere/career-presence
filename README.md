# Career Presence System

> **Automate your job search. Manage your professional presence. Land your dream role.**

A comprehensive career management platform that orchestrates job discovery, resume tailoring, application tracking, and digital presence synchronization across LinkedIn, GitHub, and personal websites.

[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20NC-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

---

## Features

### Job Search Pipeline
- **Multi-Platform Discovery** — Search LinkedIn, Indeed, Glassdoor, Google Jobs simultaneously via MCP
- **Intelligent Analysis** — Extract keywords, parse requirements, calculate match scores
- **ATS-Optimized Tailoring** — Generate role-specific resume variants with LaTeX
- **Application Tracking** — SQLite-based lifecycle management with follow-up reminders

### Digital Presence Management
- **Single Source of Truth** — All content flows from `master_profile.yaml`
- **Platform Sync** — Keep Resume, LinkedIn, GitHub, and Website consistent
- **Content Strategy** — LinkedIn post scheduling and engagement tracking

### AI-Powered Automation
- **Claude Code Integration** — Full orchestration via CLAUDE.md instructions
- **MCP Server Architecture** — Modular tools for job search, LinkedIn, GitHub, browser automation
- **Human-in-the-Loop Safety** — Confirmation required for applications and profile changes

---

## Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker (for JobSpy MCP server)

### Installation

```bash
# Clone the repository
git clone https://github.com/zahere/career-presence.git
cd career-presence

# Install with uv (recommended)
make install-dev

# Or manually
uv venv && uv pip install -e ".[dev]"
source .venv/bin/activate
```

### Configuration

```bash
# 1. Create your profile from the template
cp config/master_profile.yaml.example config/master_profile.yaml

# 2. Create credentials file
cp config/credentials.env.example config/credentials.env

# 3. Edit with your information
# - config/master_profile.yaml: Your career details
# - config/credentials.env: API keys (LinkedIn, GitHub, etc.)
```

### Build JobSpy Docker Image

```bash
cd mcp-servers/jobspy-mcp-server/jobspy
docker build -t jobspy .
```

### Run CLI

```bash
# Show available commands
uv run cps --help

# Check system status
uv run cps status

# Search for jobs
uv run cps discover "AI Engineer" --location "remote" --limit 20
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Claude Code (Orchestrator)                     │
│                     CLAUDE.md Instructions                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌───────────┬─────────┼─────────┬───────────┐
        ▼           ▼         ▼         ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ JobSpy  │ │LinkedIn │ │ GitHub  │ │Playwright│ │Filesystem│
   │  MCP    │ │  MCP    │ │  MCP    │ │  MCP    │ │  MCP    │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
        │           │           │           │           │
        └───────────┴───────────┴───────────┴───────────┘
                              │
                ┌─────────────────────────────┐
                │    master_profile.yaml      │
                │    (Single Source of Truth) │
                └─────────────────────────────┘
```

---

## CLI Commands

### Job Search

```bash
# Discover jobs across platforms
cps discover "Software Engineer" --location "San Francisco" --limit 50

# Analyze a specific job posting
cps analyze "https://example.com/job/12345"

# Generate tailored resume variant
cps tailor JOB_ID

# Score resume against job description
cps ats-score resume.pdf --job-description job.txt

# Submit application (requires confirmation)
cps apply JOB_ID --confirm
```

### Application Tracking

```bash
# View pipeline status
cps status

# Update application status
cps track APP_ID applied "Submitted via company portal"
cps track APP_ID interview "Phone screen scheduled"
cps track APP_ID offer "Received offer!"
```

### Platform Sync

```bash
# Sync all platforms from master_profile.yaml
cps sync all

# Sync specific platform
cps sync linkedin
cps sync github
cps sync resume

# Prepare all platforms for a specific job
cps prepare JOB_ID
```

---

## Project Structure

```
career-presence/
├── .mcp.json                 # MCP server configuration
├── CLAUDE.md                 # AI agent instructions
├── config/
│   ├── master_profile.yaml   # Your career data (gitignored)
│   ├── master_profile.yaml.example
│   ├── credentials.env       # API keys (gitignored)
│   ├── credentials.env.example
│   └── targets.yaml          # Target companies and roles
├── scripts/
│   ├── cli.py               # Main CLI entry point
│   ├── analysis/            # Job analysis, ATS scoring
│   ├── discovery/           # Job search integration
│   ├── tailoring/           # Resume generation
│   ├── tracking/            # Application tracking
│   ├── sync/                # Platform synchronization
│   └── ...
├── mcp-servers/
│   └── jobspy-mcp-server/   # Custom job search MCP
├── resume/
│   ├── base/                # Master LaTeX template
│   ├── templates/           # Role-specific templates
│   ├── variants/            # Generated variants (gitignored)
│   └── exports/             # PDF/DOCX output (gitignored)
├── jobs/
│   ├── discovered/          # Raw job data (gitignored)
│   ├── analyzed/            # Processed jobs (gitignored)
│   └── applied/             # Application records (gitignored)
└── tests/                   # Test suite
```

---

## MCP Servers

The system uses the [Model Context Protocol](https://modelcontextprotocol.io/) for tool integration:

| Server | Purpose | Required |
|--------|---------|----------|
| `jobspy` | Multi-platform job search (Indeed, LinkedIn, Glassdoor) | Yes |
| `linkedin` | Profile management, job applications, networking | Yes |
| `github` | Profile README, repository management | Yes |
| `playwright` | Browser automation for applications | Yes |
| `filesystem` | File operations for resume/job data | Yes |
| `fetch` | Web scraping for career pages | Optional |
| `brave-search` | Company research | Optional |

Configure servers in `.mcp.json`. See [MCP documentation](https://modelcontextprotocol.io/) for details.

---

## Development

```bash
# Run tests
make test

# Run linter
make lint

# Format code
make format

# Run all checks
make check

# Install all dependencies including AI tools
make install-all
```

---

## Configuration Reference

### master_profile.yaml

The single source of truth for your career data:

```yaml
personal:
  name: "Your Name"
  contact:
    email: "you@example.com"
    location: "City, Country"
  social:
    linkedin: "https://linkedin.com/in/you"
    github: "https://github.com/you"

summaries:
  resume: "ATS-optimized professional summary..."
  linkedin: "Conversational about section..."
  github: "Technical README content..."

experience:
  - company: "Company Name"
    role: "Your Role"
    bullets:
      - text: "Achievement with metrics"
        keywords: ["relevant", "keywords"]

skills:
  categories:
    - name: "Category"
      skills:
        - name: "Skill"
          proficiency: "expert"
```

### credentials.env

```bash
# Required
LINKEDIN_COOKIE=your_session_cookie
GITHUB_PAT=ghp_your_personal_access_token

# Optional
BRAVE_API_KEY=your_brave_api_key
OPENAI_API_KEY=sk-your_openai_key
```

---

## Security

- **Credentials** — Stored in `config/credentials.env` (gitignored)
- **Personal Data** — `master_profile.yaml` and generated content are gitignored
- **Browser Sessions** — Use separate browser profile for automation
- **Rate Limiting** — Built-in backoff to avoid account flags

---

## License

[PolyForm Noncommercial 1.0.0](LICENSE) — Free for personal and noncommercial use.

---

## Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make check`
5. Submit a pull request

---

## Acknowledgments

- [python-jobspy](https://github.com/Bunsly/JobSpy) — Multi-platform job scraping
- [Model Context Protocol](https://modelcontextprotocol.io/) — Tool integration standard
- [Claude Code](https://claude.ai/claude-code) — AI orchestration
