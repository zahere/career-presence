#!/usr/bin/env python3
"""
Career Presence System CLI

Main entry point for all career management commands.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="cps",
    help="Career Presence System - Job search, resume tailoring, and presence management",
    no_args_is_help=True,
)
console = Console()


# ═══════════════════════════════════════════════════════════════════════════
# JOB SEARCH COMMANDS
# ═══════════════════════════════════════════════════════════════════════════


@app.command()
def discover(
    query: str = typer.Argument(..., help="Search query (e.g., 'AI Engineer remote')"),
    platforms: str = typer.Option("linkedin,indeed,glassdoor", help="Platforms to search"),
    limit: int = typer.Option(25, help="Max results per platform"),
    hours: int = typer.Option(72, help="Jobs posted within this many hours"),
    location: str = typer.Option("remote", help="Location filter"),
    locale: str | None = typer.Option(
        None, help="Locale for region-specific config (e.g., 'israel')"
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
) -> None:
    """Search for jobs across platforms."""
    console.print(f"[blue]Discovering jobs:[/blue] {query}")
    console.print(f"Platforms: {platforms}, Limit: {limit}, Hours: {hours}")

    try:
        from scripts.discovery import print_summary, search_jobs

        sites = [s.strip() for s in platforms.split(",")]
        result = search_jobs(
            search_term=query,
            location=location,
            sites=sites,
            results_wanted=limit,
            hours_old=hours,
            output_format="both",
            locale=locale,
        )

        if not quiet:
            print_summary(result)

        if result.get("jobs"):
            console.print(f"\n[green]✅ Found {result['count']} jobs[/green]")
        else:
            console.print("[yellow]No jobs found matching criteria[/yellow]")

    except ImportError as e:
        console.print(f"[red]Error: Missing dependency - {e}[/red]")
        console.print("Run: pip install python-jobspy")
    except Exception as e:
        console.print(f"[red]Error during discovery: {e}[/red]")


@app.command()
def analyze(
    job_url: str = typer.Argument(..., help="URL of job posting to analyze"),
    deep: bool = typer.Option(False, "--deep", help="Perform deep analysis"),
) -> None:
    """Analyze a job posting."""
    console.print(f"[blue]Analyzing:[/blue] {job_url}")

    try:
        # For URL-based analysis, we need to fetch the job first
        # This is a simplified version - full implementation would use web fetch
        job_data = {
            "id": job_url.split("/")[-1][:10],
            "url": job_url,
            "company": "Unknown",
            "title": "Unknown",
            "description": "",
            "location": "Unknown",
        }

        # Try to extract info from URL
        if "greenhouse" in job_url or "lever" in job_url:
            job_data["company"] = job_url.split("/")[-2] if "/" in job_url else "Unknown"

        console.print("[yellow]Note: Full analysis requires job description text.[/yellow]")
        console.print("For complete analysis, use the JobSpy MCP or provide job data directly.")

        if deep:
            console.print("\n[dim]Deep analysis would include:[/dim]")
            console.print("  • Company research")
            console.print("  • Glassdoor ratings")
            console.print("  • LinkedIn company insights")
            console.print("  • Recent news")

    except ImportError as e:
        console.print(f"[red]Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Analysis error: {e}[/red]")


@app.command()
def tailor(
    job_id: str = typer.Argument(..., help="Job ID to tailor resume for"),
    template: str | None = typer.Option(None, help="Template to use"),
) -> None:
    """Generate tailored resume variant."""
    console.print(f"[blue]Tailoring resume for:[/blue] {job_id}")

    try:
        from scripts.tailoring import ResumeTailor

        tailor = ResumeTailor()

        # Load job analysis if available
        analyzed_dir = Path("jobs/analyzed")
        job_files = list(analyzed_dir.glob(f"*{job_id}*.json")) if analyzed_dir.exists() else []

        if job_files:
            with open(job_files[0]) as f:
                job_analysis = json.load(f)
            console.print(f"[green]Found job analysis: {job_files[0].name}[/green]")
        else:
            # Create minimal job analysis for demo
            job_analysis = {
                "job_id": job_id,
                "company": "Unknown",
                "role": template or "AI Engineer",
                "keywords": ["python", "kubernetes", "llm", "machine learning"],
            }
            console.print("[yellow]No job analysis found, using defaults[/yellow]")

        variant = tailor.generate_variant(job_analysis)
        tailor.save_variant_metadata(variant)

        console.print(f"\n[green]✅ Generated variant:[/green] {variant.variant_path}")
        if variant.pdf_path:
            console.print(f"[green]📄 PDF:[/green] {variant.pdf_path}")
        console.print(f"[dim]Tailoring applied: {', '.join(variant.tailoring_applied)}[/dim]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: Base resume not found - {e}[/red]")
        console.print("Ensure resume/base/master.tex exists")
    except Exception as e:
        console.print(f"[red]Tailoring error: {e}[/red]")


@app.command()
def apply(
    job_id: str = typer.Argument(..., help="Job ID to apply to"),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm submission"),
    auto: bool = typer.Option(False, "--auto", help="Auto-apply (whitelisted only)"),
) -> None:
    """Submit job application."""
    if not confirm and not auto:
        console.print("[yellow]⚠️ Add --confirm or --auto to submit[/yellow]")
        return

    console.print(f"[blue]Applying to:[/blue] {job_id}")

    try:
        from scripts.submission import apply_to_job

        result = apply_to_job(job_id, confirm=confirm)

        if result.get("status") == "submitted":
            console.print("[green]✅ Application submitted![/green]")
            if result.get("record_path"):
                console.print(f"[dim]Record: {result['record_path']}[/dim]")
        elif result.get("status") == "validation_failed":
            console.print("[red]❌ Validation failed:[/red]")
            for error in result.get("errors", []):
                console.print(f"  • {error}")
        elif result.get("status") == "awaiting_confirmation":
            console.print("[yellow]Awaiting confirmation - use --confirm to proceed[/yellow]")
        else:
            console.print(f"[yellow]Status: {result.get('status')}[/yellow]")
            if result.get("message"):
                console.print(result["message"])

    except Exception as e:
        console.print(f"[red]Application error: {e}[/red]")


# ═══════════════════════════════════════════════════════════════════════════
# RESUME COMMANDS
# ═══════════════════════════════════════════════════════════════════════════


@app.command()
def ats_score(
    resume_path: Path = typer.Argument(..., help="Path to resume PDF or LaTeX"),
    job_path: Path | None = typer.Option(None, help="Path to job description file"),
    job_text: str | None = typer.Option(None, help="Job description text"),
) -> None:
    """Calculate ATS score for resume."""
    console.print(f"[blue]Scoring:[/blue] {resume_path}")

    try:
        from scripts.analysis import ATSScorer, generate_report

        scorer = ATSScorer()

        # Get job description
        if job_path and job_path.exists():
            job_description = job_path.read_text()
        elif job_text:
            job_description = job_text
        else:
            # Use a generic AI/ML job description for baseline scoring
            job_description = """
            AI Engineer / ML Engineer position requiring:
            - Python programming
            - Machine learning / deep learning
            - Kubernetes, Docker
            - LLM, NLP experience
            - Distributed systems
            - 5+ years experience
            """
            console.print("[yellow]Using generic AI/ML job description for scoring[/yellow]")

        # Score the resume
        if resume_path.suffix.lower() == ".pdf":
            result = scorer.score_pdf(str(resume_path), job_description)
        else:
            # Assume it's a text/LaTeX file
            resume_text = resume_path.read_text()
            result = scorer.score(resume_text, job_description)

        # Print report
        report = generate_report(result)
        console.print(report)

    except FileNotFoundError:
        console.print(f"[red]Error: Resume file not found: {resume_path}[/red]")
    except Exception as e:
        console.print(f"[red]Scoring error: {e}[/red]")


# ═══════════════════════════════════════════════════════════════════════════
# TRACKING COMMANDS
# ═══════════════════════════════════════════════════════════════════════════


@app.command()
def status() -> None:
    """Display application pipeline summary."""
    try:
        from scripts.tracking import ApplicationTracker

        tracker = ApplicationTracker()
        report = tracker.generate_status_report()
        console.print(report)

    except Exception as e:
        # Fall back to basic display if tracker fails
        console.print(
            Panel.fit(
                "[green]Pipeline Status[/green]\n"
                f"├── Error loading tracker: {e}\n"
                "└── Run 'cps discover' to start finding jobs",
                title="Career Presence System",
            )
        )


@app.command()
def track(
    app_id: str = typer.Argument(..., help="Application ID"),
    action: str = typer.Argument(
        ..., help="Action: response, interview, offer, rejected, withdrawn"
    ),
    note: str | None = typer.Argument(None, help="Note or details"),
) -> None:
    """Update application status."""
    console.print(f"[blue]Tracking {app_id}:[/blue] {action}")

    try:
        from scripts.tracking import ApplicationTracker

        tracker = ApplicationTracker()

        # Map action to status
        status_map = {
            "applied": "applied",
            "response": "responded",
            "responded": "responded",
            "interview": "interviewing",
            "interviewing": "interviewing",
            "offer": "offer",
            "rejected": "rejected",
            "withdrawn": "withdrawn",
        }

        new_status = status_map.get(action.lower())
        if not new_status:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print(f"Valid actions: {', '.join(status_map.keys())}")
            return

        success = tracker.update_status(app_id, new_status, note or "")

        if success:
            console.print(f"[green]✅ Updated {app_id} to {new_status}[/green]")
            if note:
                console.print(f"[dim]Note: {note}[/dim]")
        else:
            console.print(f"[yellow]Application {app_id} not found[/yellow]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Tracking error: {e}[/red]")


# ═══════════════════════════════════════════════════════════════════════════
# SYNC COMMANDS
# ═══════════════════════════════════════════════════════════════════════════


@app.command()
def sync(
    platform: str = typer.Argument("all", help="Platform: all, resume, linkedin, github, website"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying"),
) -> None:
    """Sync platforms from master profile."""
    console.print(f"[blue]Syncing:[/blue] {platform}")

    try:
        from scripts.sync import Platform, PlatformSyncManager

        manager = PlatformSyncManager()

        if dry_run:
            console.print(f"[yellow]🔍 Dry run - would sync {platform}[/yellow]")
            console.print(f"Source: {manager.profile_path}")
            console.print(manager.get_sync_status())
            return

        # Map string to Platform enum
        platform_map = {
            "all": Platform.ALL,
            "resume": Platform.RESUME,
            "linkedin": Platform.LINKEDIN,
            "github": Platform.GITHUB,
            "website": Platform.WEBSITE,
        }

        target_platform = platform_map.get(platform.lower())
        if not target_platform:
            console.print(f"[red]Unknown platform: {platform}[/red]")
            console.print(f"Valid platforms: {', '.join(platform_map.keys())}")
            return

        results = manager.sync(target_platform)

        for result in results:
            status_icon = "✅" if result.success else "❌"
            console.print(f"\n{status_icon} {result.platform.value}")

            if result.files_updated:
                console.print(f"   Files updated: {len(result.files_updated)}")
                for f in result.files_updated[:5]:
                    console.print(f"   • {f}")
                if len(result.files_updated) > 5:
                    console.print(f"   ... and {len(result.files_updated) - 5} more")

            if result.errors:
                console.print("   [red]Errors:[/red]")
                for e in result.errors:
                    console.print(f"   ⚠️ {e}")

        console.print("\n" + manager.get_sync_status())

    except FileNotFoundError:
        console.print("[red]Error: master_profile.yaml not found[/red]")
        console.print("Create config/master_profile.yaml first")
    except Exception as e:
        console.print(f"[red]Sync error: {e}[/red]")


# ═══════════════════════════════════════════════════════════════════════════
# PRESENCE COMMANDS
# ═══════════════════════════════════════════════════════════════════════════


@app.command()
def prepare(
    job_id: str = typer.Argument(..., help="Job ID to prepare for"),
) -> None:
    """Prepare all platforms for a specific application."""
    console.print(f"[blue]Preparing for:[/blue] {job_id}")

    try:
        from scripts.linkedin import LinkedInContentManager
        from scripts.sync import Platform, PlatformSyncManager
        from scripts.tailoring import ResumeTailor

        # 1. Generate tailored resume
        console.print("\n[bold]1. Tailoring Resume[/bold]")
        tailor = ResumeTailor()

        # Load job analysis
        analyzed_dir = Path("jobs/analyzed")
        job_files = list(analyzed_dir.glob(f"*{job_id}*.json")) if analyzed_dir.exists() else []

        if job_files:
            with open(job_files[0]) as f:
                job_analysis = json.load(f)
        else:
            job_analysis = {
                "job_id": job_id,
                "company": "Unknown",
                "role": "Engineer",
                "keywords": [],
            }

        variant = tailor.generate_variant(job_analysis)
        console.print(f"   [green]✅ Resume variant: {variant.variant_path}[/green]")

        # 2. Update LinkedIn headline suggestion
        console.print("\n[bold]2. LinkedIn Optimization[/bold]")
        linkedin_mgr = LinkedInContentManager()
        headline_suggestion = linkedin_mgr.suggest_headline_update(
            job_description=job_analysis.get("raw_description", job_analysis.get("role", "")),
        )
        console.print(f"   Current: {headline_suggestion['current']}")
        console.print(f"   [yellow]Suggested: {headline_suggestion['suggested']}[/yellow]")
        console.print(f"   Reason: {headline_suggestion['reason']}")

        # 3. Sync all platforms
        console.print("\n[bold]3. Syncing Platforms[/bold]")
        sync_mgr = PlatformSyncManager()
        results = sync_mgr.sync(Platform.ALL)

        for result in results:
            status_icon = "✅" if result.success else "⚠️"
            console.print(
                f"   {status_icon} {result.platform.value}: {len(result.files_updated)} files"
            )

        console.print(f"\n[green]✅ Preparation complete for job {job_id}[/green]")

    except Exception as e:
        console.print(f"[red]Preparation error: {e}[/red]")


@app.command()
def presence(
    action: str = typer.Argument("report", help="Action: report, gaps, metrics"),
) -> None:
    """Audit digital presence."""
    console.print(f"[blue]Presence {action}[/blue]")

    try:
        if action == "report":
            # Generate presence report
            table = Table(title="Digital Presence Report")
            table.add_column("Platform", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Last Updated")
            table.add_column("Action Items")

            # Check each platform
            platforms = [
                ("Resume", "resume/base/master.tex", "Generate variants for active applications"),
                ("LinkedIn", "linkedin/profile/content.md", "Update headline, post content"),
                ("GitHub", "github/profile/README.md", "Update profile README, pin projects"),
                ("Website", "portfolio/website/src/pages/", "Deploy latest content"),
            ]

            for name, path, action_item in platforms:
                path_obj = Path(path)
                if path_obj.exists():
                    mtime = datetime.fromtimestamp(path_obj.stat().st_mtime)
                    status = "✅ Active"
                    last_updated = mtime.strftime("%Y-%m-%d")
                else:
                    status = "⚠️ Missing"
                    last_updated = "-"
                    action_item = f"Create {path}"

                table.add_row(name, status, last_updated, action_item)

            console.print(table)

        elif action == "gaps":
            console.print("\n[bold]Presence Gaps Analysis[/bold]\n")

            gaps = []

            # Check for common gaps
            if not Path("linkedin/profile/about.md").exists():
                gaps.append("LinkedIn About section not synced")
            if not Path("github/profile/README.md").exists():
                gaps.append("GitHub profile README not created")
            if not Path("resume/exports").exists() or not list(
                Path("resume/exports").glob("*.pdf")
            ):
                gaps.append("No exported resume PDFs found")
            if not Path("config/master_profile.yaml").exists():
                gaps.append("Master profile not configured")

            if gaps:
                for gap in gaps:
                    console.print(f"  [yellow]⚠️ {gap}[/yellow]")
                console.print("\n[dim]Run 'cps sync all' to address sync-related gaps[/dim]")
            else:
                console.print("[green]✅ No major gaps detected[/green]")

        elif action == "metrics":
            console.print("\n[bold]Presence Metrics[/bold]\n")
            console.print("[dim]Metrics tracking requires platform integrations.[/dim]")
            console.print("Available metrics sources:")
            console.print("  • LinkedIn: Use LinkedIn MCP for engagement data")
            console.print("  • GitHub: Use GitHub API for profile views")
            console.print("  • Applications: Run 'cps status' for pipeline metrics")

        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Valid actions: report, gaps, metrics")

    except Exception as e:
        console.print(f"[red]Presence audit error: {e}[/red]")


@app.command()
def validate() -> None:
    """Validate all configuration files."""
    console.print("[blue]Validating configuration files...[/blue]\n")

    try:
        from scripts.validation import validate_all_configs

        result = validate_all_configs()

        if result["errors"]:
            console.print("[red bold]Errors:[/red bold]")
            for error in result["errors"]:
                console.print(f"  [red]✗[/red] {error}")
            console.print()

        if result["warnings"]:
            console.print("[yellow bold]Warnings:[/yellow bold]")
            for warning in result["warnings"]:
                console.print(f"  [yellow]⚠[/yellow] {warning}")
            console.print()

        if result["valid"]:
            console.print("[green]✅ All configs valid[/green]")
        else:
            console.print("[red]❌ Config validation failed[/red]")

    except Exception as e:
        console.print(f"[red]Validation error: {e}[/red]")


def main() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
