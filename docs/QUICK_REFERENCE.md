# Career Presence System - Quick Reference

## 🎯 What This System Does

Manages your entire professional presence from a single source of truth:

```
master_profile.yaml
       │
       ├──► Resume (LaTeX, ATS-optimized, role-tailored)
       ├──► LinkedIn (Profile, Posts, Content Strategy)
       ├──► GitHub (Profile README, Repo Showcases)
       ├──► Website (Portfolio, Blog, Contact)
       └──► Job Search (Discover, Apply, Track)
```

## 📁 Project Structure

```
career-presence/
├── config/
│   └── master_profile.yaml    # ⭐ Single source of truth
├── resume/
│   ├── base/master.tex        # Master LaTeX resume
│   └── variants/              # Generated role-specific versions
├── linkedin/
│   ├── profile/               # Profile content (about, experience)
│   └── posts/                 # Content drafts and calendar
├── github/
│   └── profile/README.md      # Profile README
├── website/
│   └── src/                   # Portfolio website source
├── scripts/
│   ├── sync/platform_sync.py  # Cross-platform sync
│   ├── linkedin/content_manager.py
│   ├── website/generator.py
│   ├── analysis/ats_scorer.py
│   └── tailoring/resume_tailor.py
└── CLAUDE.md                  # Agent instructions
```

## 🚀 Quick Start

```bash
# 1. Set up credentials
export GITHUB_PAT="your_github_token"
export LINKEDIN_COOKIE="your_linkedin_cookie"

# 2. Sync all platforms from master profile
python scripts/sync/platform_sync.py all

# 3. Generate content calendar
python scripts/linkedin/content_manager.py calendar --weeks 4

# 4. Start job search
/discover AI Engineer remote
```

## 📝 Command Reference

### Platform Sync
```bash
/sync all              # Sync all platforms
/sync resume           # Sync resume only
/sync linkedin         # Sync LinkedIn only
/sync github           # Sync GitHub only
/sync website          # Sync website only
/sync status           # Check sync status
```

### Resume Management
```bash
/resume generate [job_id]    # Generate tailored variant
/resume score [job_id]       # Calculate ATS score
/resume export pdf           # Export to PDF
```

### LinkedIn Management
```bash
/linkedin optimize           # Profile optimization suggestions
/linkedin post draft [type]  # Create post draft
/linkedin calendar           # View/generate content calendar
/linkedin ideas              # Get post ideas
```

### GitHub Management
```bash
/github readme update        # Update profile README
/github repo optimize [repo] # Optimize repo presentation
/github topics [repo]        # Suggest topics
```

### Website Management
```bash
/website build               # Build static site
/website deploy              # Deploy to hosting
/website blog new [title]    # Create blog post
```

### Job Search
```bash
/discover [criteria]         # Search for jobs
/analyze [job_url]           # Deep analysis
/tailor [job_id]             # Generate resume
/apply [job_id]              # Submit application
/track [app_id] [action]     # Update tracking
/status                      # Pipeline overview
```

## 📊 Platform Optimization Checklist

### Resume
- [ ] Professional summary tailored to role
- [ ] Metrics in every bullet point
- [ ] ATS score 80%+ for target jobs
- [ ] Clean, single-column format
- [ ] PDF exports correctly

### LinkedIn
- [ ] Headline: Role + Project + Value (120-150 chars)
- [ ] About: Hook + Story + Skills + CTA (2000+ chars)
- [ ] All experience with metrics
- [ ] Top 3 skills pinned
- [ ] Featured section with projects
- [ ] Custom URL claimed
- [ ] Profile photo professional

### GitHub
- [ ] Profile README with stats
- [ ] Top repos pinned
- [ ] All repos have descriptions
- [ ] Topics on key repos
- [ ] Consistent commit activity
- [ ] AgentiCraft well-documented

### Website
- [ ] Homepage with clear CTA
- [ ] Projects showcase with demos
- [ ] Blog with technical content
- [ ] Resume download available
- [ ] Mobile responsive
- [ ] Fast load times

## 📅 Weekly Routine

| Day | Focus |
|-----|-------|
| **Mon** | Job discovery, application review |
| **Tue** | LinkedIn content creation |
| **Wed** | GitHub maintenance |
| **Thu** | Resume variants for applications |
| **Fri** | Analytics review, networking |
| **Sat** | Blog writing, deep work |
| **Sun** | Planning, sync check |

## 🔧 MCP Servers Required

| Server | Purpose | Setup |
|--------|---------|-------|
| `github` | Profile, repos | `npm i -g @modelcontextprotocol/server-github` |
| `linkedin` | Profile, jobs | `docker pull stickerdaniel/linkedin-mcp-server` |
| `jobspy` | Multi-platform search | `npm install` in jobspy-mcp-server |
| `playwright` | Browser automation | `npm i -g @playwright/mcp` |
| `filesystem` | File management | Built-in |

## 📈 Success Metrics

| Metric | Target |
|--------|--------|
| LinkedIn Profile Views | 100+/week |
| Post Impressions | 1000+/post |
| GitHub Profile Views | Track growth |
| Applications Sent | 10-20/week |
| Response Rate | 15%+ |
| Interview Rate | 10%+ |

## ⚠️ Rate Limits

| Platform | Limit |
|----------|-------|
| LinkedIn MCP | 100 actions/day |
| GitHub API | 5000 requests/hour |
| Applications | 5/hour, 20/day |
| Posts | 1/day max |

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| LinkedIn auth expired | `uvx linkedin-scraper-mcp --get-session` |
| GitHub PAT expired | Generate new at github.com/settings/tokens |
| Sync failed | Check `scripts/sync/` logs |
| LaTeX compile error | Verify pdflatex installed |

---

**Remember**: Quality > Quantity. 5 great applications beat 50 generic ones.
