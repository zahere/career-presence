#!/usr/bin/env python3
"""
Job Search Script using python-jobspy
Multi-platform job discovery: LinkedIn, Indeed, Glassdoor, ZipRecruiter
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime
from pathlib import Path

import yaml
from jobspy import scrape_jobs

# Configuration paths
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def _merge_locale(base: dict, overrides: dict) -> dict:
    """
    Merge locale-specific overrides into a base targets config.

    Merge strategy:
    - tiers: extend (append locale companies to base tier lists)
    - bad_words: extend (append locale words, deduplicate)
    - locations: replace (locale provides its own location lists)
    - salary/country: replace (locale value wins)
    - Everything else (target_roles, experience_range): inherited from base

    Args:
        base: Base targets dict (without the ``locales`` key).
        overrides: Locale-specific overrides dict.

    Returns:
        New merged dict. *base* is never mutated.
    """
    merged = copy.deepcopy(base)

    # --- tiers: extend ---
    locale_tiers = overrides.get("tiers", {})
    for tier_name, tier_data in locale_tiers.items():
        locale_companies = tier_data.get("companies", [])
        if tier_name in merged.get("tiers", {}):
            merged["tiers"][tier_name]["companies"] = (
                merged["tiers"][tier_name].get("companies", []) + locale_companies
            )
        else:
            merged.setdefault("tiers", {})[tier_name] = {"companies": locale_companies}

    # --- bad_words: extend + deduplicate ---
    locale_bw = overrides.get("bad_words", {})
    for key in ("title_words", "description_words"):
        if key in locale_bw:
            existing = merged.get("bad_words", {}).get(key, [])
            combined = existing + locale_bw[key]
            # Deduplicate preserving order
            seen: set[str] = set()
            deduped: list[str] = []
            for w in combined:
                low = w.lower()
                if low not in seen:
                    seen.add(low)
                    deduped.append(w)
            merged.setdefault("bad_words", {})[key] = deduped

    # --- search_params: locations=replace, salary=replace, country=replace ---
    locale_sp = overrides.get("search_params", {})
    if "locations" in locale_sp:
        merged.setdefault("search_params", {})["locations"] = locale_sp["locations"]
    if "salary" in locale_sp:
        merged.setdefault("search_params", {})["salary"] = locale_sp["salary"]
    if "country" in locale_sp:
        merged.setdefault("search_params", {})["country"] = locale_sp["country"]

    return merged


def load_targets(locale: str | None = None) -> dict:
    """
    Load target companies and search parameters from config.

    Args:
        locale: Optional locale name (e.g. ``"israel"``). When provided,
                the matching ``locales.<name>`` section is merged into the
                base config using :func:`_merge_locale`.

    Returns:
        Dictionary with target companies and search configuration.

    Raises:
        ValueError: If *locale* is specified but not found in config.
    """
    targets_path = CONFIG_DIR / "targets.yaml"
    if not targets_path.exists():
        return {}

    with open(targets_path) as f:
        raw = yaml.safe_load(f) or {}

    # Pop locales section out — callers never see it in the merged dict
    locales = raw.pop("locales", {})

    if locale is None:
        return raw

    if locale not in locales:
        raise ValueError(
            f"Unknown locale '{locale}'. Available locales: {', '.join(locales) or '(none)'}"
        )

    return _merge_locale(raw, locales[locale])


def _extract_experience_years(text: str) -> int | None:
    """
    Extract required years of experience from job text.

    Looks for patterns like "5+ years", "3-5 years of experience",
    "minimum 7 years", etc.

    Returns the primary number found, or None if no match.
    """
    if not text:
        return None

    patterns = [
        # Range pattern first: "3-5 years" → captures the lower bound (3)
        r"(\d+)\s*-\s*\d+\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
        r"(?:minimum|at least|min)\s*(\d+)\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
        r"(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:professional|relevant|hands-on|industry)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue

    return None


def apply_targets_filter(jobs: list[dict], targets: dict) -> list[dict]:
    """
    Apply targets configuration to job list.

    - Adds tier info (tier1/tier2/tier3/unknown)
    - Adds priority score
    - Adds auto_apply eligibility
    - Filters out exclusions
    - Applies bad word penalties (soft filter)
    - Checks experience range match

    Args:
        jobs: List of job dictionaries
        targets: Loaded targets.yaml configuration

    Returns:
        Filtered and enriched job list
    """
    if not targets:
        return jobs

    # Build company lookup
    company_tiers = {}
    for tier_name in ["tier1", "tier2", "tier3"]:
        tier_data = targets.get("tiers", {}).get(tier_name, {})
        for company in tier_data.get("companies", []):
            company_name = company.get("name", "").lower()
            company_tiers[company_name] = {
                "tier": tier_name,
                "priority": company.get("priority", 3),
                "auto_apply": tier_name in ["tier1", "tier2"],
                "careers_url": company.get("careers_url"),
            }

    # Get exclusions
    exclusions = targets.get("exclusions", {})
    excluded_companies = [c.lower() for c in exclusions.get("companies", [])]
    excluded_keywords = [k.lower() for k in exclusions.get("keywords", [])]

    # Get target roles
    target_roles = targets.get("target_roles", {})
    primary_roles = [r.lower() for r in target_roles.get("primary", [])]
    secondary_roles = [r.lower() for r in target_roles.get("secondary", [])]

    # Get bad words config
    bad_words_config = targets.get("bad_words", {})
    bad_title_words = [w.lower() for w in bad_words_config.get("title_words", [])]
    bad_desc_words = [w.lower() for w in bad_words_config.get("description_words", [])]
    penalty_per_match = bad_words_config.get("penalty_per_match", 5.0)

    # Get experience range config
    exp_range = targets.get("experience_range", {})
    exp_min = exp_range.get("min_years", 0)
    exp_max = exp_range.get("max_years", 50)

    enriched_jobs = []
    for job in jobs:
        company = (job.get("company") or "").lower()
        title = (job.get("title") or "").lower()
        description = (job.get("description") or "").lower()

        # Check exclusions (hard filter)
        if company in excluded_companies:
            continue
        if any(kw in title or kw in description for kw in excluded_keywords):
            continue

        # Add tier info
        tier_info = company_tiers.get(
            company,
            {
                "tier": "unknown",
                "priority": 4,
                "auto_apply": False,
            },
        )
        job["target_tier"] = tier_info["tier"]
        job["target_priority"] = tier_info["priority"]
        job["auto_apply_eligible"] = tier_info["auto_apply"]

        # Check role match
        if any(role in title for role in primary_roles):
            job["role_match"] = "primary"
            job["target_priority"] = min(job["target_priority"], 1)
        elif any(role in title for role in secondary_roles):
            job["role_match"] = "secondary"
            job["target_priority"] = min(job["target_priority"], 2)
        else:
            job["role_match"] = "other"

        # Bad word penalty scoring (soft filter)
        bad_word_penalty = 0.0
        matched_bad_words = []

        for word in bad_title_words:
            if word in title:
                bad_word_penalty += penalty_per_match
                matched_bad_words.append(f"title:{word}")

        for word in bad_desc_words:
            if word in description:
                bad_word_penalty += penalty_per_match
                matched_bad_words.append(f"desc:{word}")

        job["bad_word_penalty"] = bad_word_penalty
        job["bad_words_matched"] = matched_bad_words

        # Experience range check
        required_years = _extract_experience_years(description) or _extract_experience_years(title)
        if required_years is not None:
            job["required_experience_years"] = required_years
            if exp_min <= required_years <= exp_max:
                job["experience_match"] = "in_range"
            elif required_years < exp_min:
                job["experience_match"] = "under_qualified"
                job["bad_word_penalty"] = job.get("bad_word_penalty", 0) + penalty_per_match
            else:
                job["experience_match"] = "over_qualified"
                job["bad_word_penalty"] = job.get("bad_word_penalty", 0) + penalty_per_match
        else:
            job["experience_match"] = "unknown"

        enriched_jobs.append(job)

    # Sort by priority (lower is better), then by penalty (lower is better)
    enriched_jobs.sort(
        key=lambda j: (
            j.get("target_priority", 4),
            j.get("bad_word_penalty", 0),
            j.get("target_tier", "z"),
        )
    )

    return enriched_jobs


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    """
    Remove duplicate job postings.

    Matches by:
    - job_url (exact match)
    - (company + role + location) combination

    Args:
        jobs: List of job dictionaries

    Returns:
        List of unique job dictionaries
    """
    seen = set()
    unique_jobs = []

    for job in jobs:
        # Create unique key
        url_key = job.get("job_url") or job.get("url", "")
        combo_key = f"{job.get('company', '')}|{job.get('title', '')}|{job.get('location', '')}"

        if url_key and url_key in seen:
            continue
        if combo_key in seen:
            continue

        seen.add(url_key)
        seen.add(combo_key)
        unique_jobs.append(job)

    return unique_jobs


def search_jobs(
    search_term: str = "AI Engineer",
    location: str = "remote",
    sites: list[str] | None = None,
    results_wanted: int = 25,
    hours_old: int = 72,
    country: str = "USA",
    is_remote: bool = True,
    output_format: str = "both",
    locale: str | None = None,
) -> dict:
    """
    Search for jobs across multiple platforms.

    Args:
        search_term: Job title or keywords to search
        location: Location filter (city, state, or "remote")
        sites: List of sites to search (linkedin, indeed, glassdoor, zip_recruiter)
        results_wanted: Number of results per site
        hours_old: Only show jobs posted within this many hours
        country: Country code for job search
        is_remote: Filter for remote jobs only
        output_format: "json", "csv", or "both"
        locale: Optional locale name (e.g. "israel") for region-specific config

    Returns:
        Dictionary with search results and metadata
    """
    if sites is None:
        sites = ["linkedin", "indeed", "glassdoor"]

    # Apply locale overrides for location/country when caller used defaults
    if locale:
        targets_for_defaults = load_targets(locale=locale)
        sp = targets_for_defaults.get("search_params", {})
        if location == "remote":
            preferred = sp.get("locations", {}).get("preferred", [])
            if preferred:
                location = preferred[0]
        if country == "USA":
            country = sp.get("country", country)
        if locale:
            print(f"  Locale: {locale}")

    print(f"Searching for '{search_term}' jobs...")
    print(f"  Location: {location}")
    print(f"  Sites: {', '.join(sites)}")
    print(f"  Results wanted: {results_wanted}")
    print(f"  Posted within: {hours_old} hours")
    print()

    try:
        jobs_df = scrape_jobs(
            site_name=sites,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=country,
            is_remote=is_remote,
        )
    except Exception as e:
        print(f"Error during search: {e}")
        return {"error": str(e), "jobs": []}

    if jobs_df.empty:
        print("No jobs found matching criteria.")
        return {"jobs": [], "count": 0}

    # Convert to records
    jobs_list = jobs_df.to_dict(orient="records")

    # Clean up NaN values for JSON serialization
    for job in jobs_list:
        for key, value in job.items():
            if isinstance(value, float) and str(value) == "nan":
                job[key] = None

    # Deduplicate jobs
    jobs_list = deduplicate_jobs(jobs_list)

    # Apply targets configuration (tier info, priority, exclusions)
    targets = load_targets(locale=locale)
    if targets:
        original_count = len(jobs_list)
        jobs_list = apply_targets_filter(jobs_list, targets)
        filtered_count = original_count - len(jobs_list)
        if filtered_count > 0:
            print(f"Filtered {filtered_count} jobs based on exclusions")

        # Count by tier
        tier_counts: dict[str, int] = {}
        for job in jobs_list:
            tier = job.get("target_tier", "unknown")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        print(f"Jobs by tier: {tier_counts}")

    # Filter out already-applied jobs via DB lookup
    try:
        from scripts.tracking import ApplicationTracker

        tracker = ApplicationTracker()
        jobs_list, already_applied = tracker.filter_already_applied(jobs_list)
        if already_applied:
            print(f"Filtered {len(already_applied)} already-applied jobs (DB dedup)")
    except Exception as e:
        # Non-fatal: continue without DB dedup if tracker is unavailable
        print(f"Note: DB dedup skipped ({e})")

    result = {
        "search_term": search_term,
        "location": location,
        "sites": sites,
        "timestamp": datetime.now().isoformat(),
        "count": len(jobs_list),
        "jobs": jobs_list,
    }

    # Save outputs
    output_dir = Path(__file__).parent.parent.parent / "jobs" / "discovered"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"jobs_{search_term.replace(' ', '_').lower()}_{timestamp}"

    if output_format in ("json", "both"):
        json_path = output_dir / f"{base_name}.json"
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Saved JSON: {json_path}")

    if output_format in ("csv", "both"):
        csv_path = output_dir / f"{base_name}.csv"
        jobs_df.to_csv(csv_path, index=False)
        print(f"Saved CSV: {csv_path}")

    return result


def print_summary(result: dict) -> None:
    """Print a formatted summary of search results."""
    if "error" in result:
        print(f"Search failed: {result['error']}")
        return

    jobs = result.get("jobs", [])
    print(f"\n{'=' * 70}")
    print(f"Found {len(jobs)} jobs for '{result.get('search_term', 'N/A')}'")
    print(f"{'=' * 70}\n")

    for i, job in enumerate(jobs[:15], 1):  # Show top 15
        title = job.get("title", "N/A")
        company = job.get("company", "N/A")
        location = job.get("location", "N/A")
        site = job.get("site", "N/A")
        url = job.get("job_url", "")
        tier = job.get("target_tier", "")
        role_match = job.get("role_match", "")

        tier_badge = f" [{tier.upper()}]" if tier and tier != "unknown" else ""
        role_badge = f" ({role_match})" if role_match and role_match != "other" else ""

        print(f"{i:2}. {title}{role_badge}")
        print(f"    Company:  {company}{tier_badge}")
        print(f"    Location: {location}")
        print(f"    Source:   {site}")
        if url:
            print(f"    URL:      {url[:80]}...")
        print()

    if len(jobs) > 15:
        print(f"... and {len(jobs) - 15} more jobs (see saved files)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search for jobs across multiple platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "AI Engineer" --location remote
  %(prog)s "ML Engineer" --location "San Francisco, CA" --sites linkedin indeed
  %(prog)s "Data Scientist" --results 50 --hours 24
        """,
    )

    parser.add_argument(
        "search_term",
        nargs="?",
        default="AI Engineer",
        help="Job title or keywords to search (default: 'AI Engineer')",
    )
    parser.add_argument(
        "-l",
        "--location",
        default="remote",
        help="Location filter (default: 'remote')",
    )
    parser.add_argument(
        "-s",
        "--sites",
        nargs="+",
        choices=["linkedin", "indeed", "glassdoor", "zip_recruiter"],
        default=["linkedin", "indeed", "glassdoor"],
        help="Sites to search (default: linkedin indeed glassdoor)",
    )
    parser.add_argument(
        "-r",
        "--results",
        type=int,
        default=25,
        help="Number of results wanted per site (default: 25)",
    )
    parser.add_argument(
        "-t",
        "--hours",
        type=int,
        default=72,
        help="Only jobs posted within this many hours (default: 72)",
    )
    parser.add_argument(
        "-c",
        "--country",
        default="USA",
        help="Country for job search (default: USA)",
    )
    parser.add_argument(
        "--include-onsite",
        action="store_true",
        help="Include on-site jobs (default: remote only)",
    )
    parser.add_argument(
        "--locale",
        default=None,
        help="Locale for region-specific config (e.g., 'israel')",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Minimal output (no summary)",
    )

    args = parser.parse_args()

    result = search_jobs(
        search_term=args.search_term,
        location=args.location,
        sites=args.sites,
        results_wanted=args.results,
        hours_old=args.hours,
        country=args.country,
        is_remote=not args.include_onsite,
        output_format=args.format,
        locale=args.locale,
    )

    if not args.quiet:
        print_summary(result)

    # Exit with error code if no results
    return 0 if result.get("jobs") else 1


if __name__ == "__main__":
    exit(main())
