#!/usr/bin/env python3
"""
Application Tracking Database Manager
SQLite-based tracking for job applications
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Application:
    """Represents a job application"""

    id: str
    company: str
    role: str
    job_url: str
    platform: str  # linkedin, greenhouse, lever, direct

    status: str  # discovered, analyzing, ready, applied, responded, interviewing, offer, rejected
    match_score: float

    resume_variant: str | None
    cover_letter: str | None

    salary_range: str | None
    location: str
    remote_policy: str

    applied_at: str | None
    response_at: str | None

    keywords_matched: list[str]
    notes: str

    created_at: str
    updated_at: str


class ApplicationTracker:
    """
    Manages application tracking database
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS applications (
        id TEXT PRIMARY KEY,
        company TEXT NOT NULL,
        role TEXT NOT NULL,
        job_url TEXT,
        platform TEXT,

        status TEXT DEFAULT 'discovered',
        match_score REAL,

        resume_variant TEXT,
        cover_letter TEXT,

        salary_range TEXT,
        location TEXT,
        remote_policy TEXT,

        applied_at TEXT,
        response_at TEXT,

        keywords_matched TEXT,  -- JSON array
        notes TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT REFERENCES applications(id),
        type TEXT,  -- application, email, phone, interview, offer, rejection
        details TEXT,
        occurred_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS job_cache (
        job_id TEXT PRIMARY KEY,
        company TEXT,
        role TEXT,
        job_url TEXT,
        platform TEXT,
        raw_data TEXT,  -- JSON
        fetched_at TEXT,
        expires_at TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
    CREATE INDEX IF NOT EXISTS idx_applications_company ON applications(company);
    CREATE INDEX IF NOT EXISTS idx_interactions_app_id ON interactions(application_id);
    CREATE INDEX IF NOT EXISTS idx_applications_job_url ON applications(job_url);
    """

    STATUS_FLOW = [
        "discovered",
        "analyzing",
        "ready",
        "applied",
        "responded",
        "interviewing",
        "offer",
        "rejected",
        "withdrawn",
    ]

    def __init__(self, db_path: str = "data/applications.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database with schema"""
        with self._get_connection() as conn:
            conn.executescript(self.SCHEMA)

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def is_already_applied(
        self,
        company: str,
        role: str,
        job_url: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Check if we've already applied to this job.

        Checks by job_url first (exact match), then by company+role (fuzzy).
        Ignores applications that are only in 'discovered' status.

        Returns:
            The existing application dict if found, None otherwise.
        """
        with self._get_connection() as conn:
            # Check by URL first (most reliable)
            if job_url:
                row = conn.execute(
                    """
                    SELECT * FROM applications
                    WHERE job_url = ? AND status != 'discovered'
                    LIMIT 1
                    """,
                    (job_url,),
                ).fetchone()
                if row:
                    return self._row_to_dict(row)

            # Check by company + role (case-insensitive)
            if company and role:
                row = conn.execute(
                    """
                    SELECT * FROM applications
                    WHERE LOWER(company) = LOWER(?) AND LOWER(role) = LOWER(?)
                    AND status != 'discovered'
                    LIMIT 1
                    """,
                    (company, role),
                ).fetchone()
                if row:
                    return self._row_to_dict(row)

        return None

    def filter_already_applied(
        self, jobs: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Partition a job list into new and already-applied jobs.

        Args:
            jobs: List of job dicts (must have 'company', 'title'/'role', optional 'job_url')

        Returns:
            Tuple of (new_jobs, already_applied)
        """
        new_jobs = []
        already_applied = []

        for job in jobs:
            company = job.get("company", "")
            role = job.get("title") or job.get("role", "")
            job_url = job.get("job_url") or job.get("url")

            existing = self.is_already_applied(company, role, job_url)
            if existing:
                job["already_applied"] = True
                job["existing_application_id"] = existing.get("id")
                job["existing_status"] = existing.get("status")
                already_applied.append(job)
            else:
                new_jobs.append(job)

        return new_jobs, already_applied

    def add_application(self, app: Application) -> bool:
        """Add a new application"""
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO applications (
                        id, company, role, job_url, platform,
                        status, match_score,
                        resume_variant, cover_letter,
                        salary_range, location, remote_policy,
                        applied_at, response_at,
                        keywords_matched, notes,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        app.id,
                        app.company,
                        app.role,
                        app.job_url,
                        app.platform,
                        app.status,
                        app.match_score,
                        app.resume_variant,
                        app.cover_letter,
                        app.salary_range,
                        app.location,
                        app.remote_policy,
                        app.applied_at,
                        app.response_at,
                        json.dumps(app.keywords_matched),
                        app.notes,
                        app.created_at,
                        app.updated_at,
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def update_status(self, app_id: str, new_status: str, notes: str = "") -> bool:
        """Update application status"""
        if new_status not in self.STATUS_FLOW:
            raise ValueError(f"Invalid status: {new_status}")

        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE applications
                SET status = ?, updated_at = ?, notes = COALESCE(notes || '\n' || ?, notes)
                WHERE id = ?
            """,
                (new_status, now, notes, app_id),
            )

            # Record interaction
            if new_status == "applied":
                conn.execute(
                    """
                    UPDATE applications SET applied_at = ? WHERE id = ?
                """,
                    (now, app_id),
                )
            elif new_status in ["responded", "interviewing", "offer", "rejected"]:
                conn.execute(
                    """
                    UPDATE applications SET response_at = ? WHERE id = ?
                """,
                    (now, app_id),
                )

            return cursor.rowcount > 0

    def add_interaction(
        self, app_id: str, interaction_type: str, details: str, occurred_at: str | None = None
    ) -> int:
        """Add an interaction record"""
        occurred_at = occurred_at or datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO interactions (application_id, type, details, occurred_at)
                VALUES (?, ?, ?, ?)
            """,
                (app_id, interaction_type, details, occurred_at),
            )
            return cursor.lastrowid or 0

    def get_application(self, app_id: str) -> dict[str, Any] | None:
        """Get a single application by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM applications WHERE id = ?
            """,
                (app_id,),
            ).fetchone()

            if row:
                return self._row_to_dict(row)
            return None

    def get_applications_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get all applications with a specific status"""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM applications WHERE status = ?
                ORDER BY updated_at DESC
            """,
                (status,),
            ).fetchall()

            return [self._row_to_dict(row) for row in rows]

    def get_all_applications(self) -> list[dict[str, Any]]:
        """Get all applications"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM applications ORDER BY updated_at DESC
            """).fetchall()

            return [self._row_to_dict(row) for row in rows]

    def get_pipeline_stats(self) -> dict[str, int]:
        """Get counts by status"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM applications
                GROUP BY status
            """).fetchall()

            return {row["status"]: row["count"] for row in rows}

    def get_interactions(self, app_id: str) -> list[dict[str, Any]]:
        """Get all interactions for an application"""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM interactions
                WHERE application_id = ?
                ORDER BY occurred_at DESC
            """,
                (app_id,),
            ).fetchall()

            return [dict(row) for row in rows]

    def search_applications(
        self, company: str | None = None, role: str | None = None, min_score: float | None = None
    ) -> list[dict[str, Any]]:
        """Search applications with filters"""
        query = "SELECT * FROM applications WHERE 1=1"
        params: list[str | float] = []

        if company:
            query += " AND company LIKE ?"
            params.append(f"%{company}%")

        if role:
            query += " AND role LIKE ?"
            params.append(f"%{role}%")

        if min_score is not None:
            query += " AND match_score >= ?"
            params.append(min_score)

        query += " ORDER BY match_score DESC, updated_at DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert database row to dictionary"""
        d = dict(row)
        if d.get("keywords_matched"):
            d["keywords_matched"] = json.loads(d["keywords_matched"])
        return d

    def get_analytics(self) -> dict[str, Any]:
        """Get application analytics"""
        with self._get_connection() as conn:
            # Overall stats
            stats = self.get_pipeline_stats()

            # Response rate
            applied_count = (
                stats.get("applied", 0)
                + stats.get("responded", 0)
                + stats.get("interviewing", 0)
                + stats.get("offer", 0)
                + stats.get("rejected", 0)
            )
            responded_count = (
                stats.get("responded", 0)
                + stats.get("interviewing", 0)
                + stats.get("offer", 0)
                + stats.get("rejected", 0)
            )

            response_rate = (responded_count / applied_count * 100) if applied_count > 0 else 0

            # Top companies
            top_companies = conn.execute("""
                SELECT company, COUNT(*) as count
                FROM applications
                GROUP BY company
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()

            # Average match score by status
            avg_scores = conn.execute("""
                SELECT status, AVG(match_score) as avg_score
                FROM applications
                GROUP BY status
            """).fetchall()

            return {
                "pipeline_stats": stats,
                "response_rate": round(response_rate, 1),
                "total_applications": sum(stats.values()),
                "top_companies": [dict(row) for row in top_companies],
                "avg_score_by_status": {
                    row["status"]: round(row["avg_score"], 1)
                    for row in avg_scores
                    if row["avg_score"]
                },
            }

    def export_to_csv(self, filepath: str) -> None:
        """Export applications to CSV"""
        import csv

        applications = self.get_all_applications()

        if not applications:
            return

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=applications[0].keys())
            writer.writeheader()
            writer.writerows(applications)

    def generate_status_report(self) -> str:
        """Generate a text status report"""
        stats = self.get_pipeline_stats()
        analytics = self.get_analytics()

        report = f"""
╔════════════════════════════════════════════════════════════════╗
║                    APPLICATION PIPELINE STATUS                  ║
╠════════════════════════════════════════════════════════════════╣
║  Total Applications: {analytics["total_applications"]:<4}                                    ║
║  Response Rate: {analytics["response_rate"]}%                                        ║
╠════════════════════════════════════════════════════════════════╣
║  Pipeline Breakdown:                                            ║
║  ├── Discovered:    {stats.get("discovered", 0):<4}                                    ║
║  ├── Analyzing:     {stats.get("analyzing", 0):<4}                                    ║
║  ├── Ready:         {stats.get("ready", 0):<4}                                    ║
║  ├── Applied:       {stats.get("applied", 0):<4}                                    ║
║  ├── Responded:     {stats.get("responded", 0):<4}                                    ║
║  ├── Interviewing:  {stats.get("interviewing", 0):<4}                                    ║
║  ├── Offers:        {stats.get("offer", 0):<4}                                    ║
║  └── Rejected:      {stats.get("rejected", 0):<4}                                    ║
╠════════════════════════════════════════════════════════════════╣
║  Top Companies:                                                 ║"""

        for company_data in analytics["top_companies"][:5]:
            report += f"\n║  • {company_data['company'][:30]:<30} ({company_data['count']})"

        report += """
╚════════════════════════════════════════════════════════════════╝
"""
        return report


def main() -> None:
    """Example usage"""
    tracker = ApplicationTracker()

    # Create sample application
    app = Application(
        id="app_12345",
        company="Anthropic",
        role="AI Research Engineer",
        job_url="https://boards.greenhouse.io/anthropic/jobs/12345",
        platform="greenhouse",
        status="discovered",
        match_score=85.5,
        resume_variant=None,
        cover_letter=None,
        salary_range="$200,000 - $350,000",
        location="San Francisco, CA",
        remote_policy="remote_friendly",
        applied_at=None,
        response_at=None,
        keywords_matched=["python", "llm", "distributed systems"],
        notes="High priority target company",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    # Add application
    tracker.add_application(app)

    # Update status
    tracker.update_status("app_12345", "analyzing", "Started job analysis")
    tracker.update_status("app_12345", "ready", "Resume variant generated")

    # Add interaction
    tracker.add_interaction("app_12345", "note", "Strong alignment with AgentiCraft work")

    # Get stats
    print(tracker.generate_status_report())

    # Get analytics
    analytics = tracker.get_analytics()
    print(f"Total applications: {analytics['total_applications']}")


if __name__ == "__main__":
    main()
