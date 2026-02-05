#!/usr/bin/env python3
"""
LinkedIn Content Manager

Manages LinkedIn content strategy:
- Post templates and drafts
- Content calendar and scheduling
- Engagement tracking
- Profile optimization recommendations
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any


class PostType(Enum):
    TECHNICAL_INSIGHT = "technical_insight"
    BUILD_IN_PUBLIC = "build_in_public"
    INDUSTRY_COMMENTARY = "industry_commentary"
    CAREER_UPDATE = "career_update"
    ENGAGEMENT = "engagement"
    ANNOUNCEMENT = "announcement"
    TUTORIAL = "tutorial"
    CASE_STUDY = "case_study"


@dataclass
class LinkedInPost:
    """Represents a LinkedIn post"""

    id: str
    type: PostType
    title: str
    content: str
    hashtags: list[str]
    scheduled_date: datetime | None
    status: str  # draft, scheduled, published
    engagement: dict | None  # likes, comments, shares
    created_at: datetime

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        d["scheduled_date"] = self.scheduled_date.isoformat() if self.scheduled_date else None
        d["created_at"] = self.created_at.isoformat()
        return d


class LinkedInContentManager:
    """
    Manages LinkedIn content creation and scheduling.
    """

    HASHTAG_SETS = {
        "primary": ["#AI", "#MachineLearning", "#LLM"],
        "secondary": ["#MultiAgentSystems", "#AIEngineering", "#MLOps", "#BuildInPublic"],
        "niche": ["#RAG", "#LLMOps", "#Kubernetes", "#DistributedSystems"],
    }

    # Content hooks (attention grabbers) - merged from content_generator.py
    HOOKS = {
        "multi_agent": [
            "Multi-agent systems don't fail gracefully. They fail spectacularly.",
            "The hardest part of building agent systems isn't the AI. It's everything else.",
            "Your agent orchestrator is the new monolith.",
            "LangGraph and CrewAI are great... until you need enterprise features.",
        ],
        "llmops": [
            "Your LLM costs are 3x what they should be.",
            "Observability for AI is not optional anymore.",
            "The gap between demo and production is a chasm.",
            "Your prompt is probably not the problem.",
        ],
        "career": [
            "The best career advice I ignored (and why I regret it)",
            "What I wish I knew before my first AI job",
            "Why I left a stable job to build my own project",
        ],
    }

    POST_TEMPLATES = {
        PostType.TECHNICAL_INSIGHT: """
{hook}

I've been working on {topic} for {time_period}, and here's what I learned:

1. {insight_1_emoji} {insight_1}
   {explanation_1}

2. {insight_2_emoji} {insight_2}
   {explanation_2}

3. {insight_3_emoji} {insight_3}
   {explanation_3}

The biggest surprise? {personal_reflection}

What's been your experience with {topic_question}?

{hashtags}
""",
        PostType.BUILD_IN_PUBLIC: """
Week {week_number} of building {project_name}:

This week I {main_accomplishment}.

🎯 What I shipped:
• {shipped_1}
• {shipped_2}
• {shipped_3}

🧠 What I learned:
{key_learning}

⏭️ Next week:
{next_week_plan}

If you're building something similar, I'd love to hear your approach to {challenge_question}.

{hashtags}
""",
        PostType.INDUSTRY_COMMENTARY: """
{hot_take}

Here's why I think this:

{reasoning_paragraph}

{supporting_evidence}

But I could be wrong. What do you think?

{hashtags}
""",
        PostType.ANNOUNCEMENT: """
🚀 {announcement}

{context}

Why this matters:
• {reason_1}
• {reason_2}
• {reason_3}

{call_to_action}

{hashtags}
""",
        PostType.ENGAGEMENT: """
{question_or_poll}

I've been thinking about {topic} lately.

{personal_context}

Curious to hear different perspectives:

{option_1}
{option_2}
{option_3}

Drop your thoughts below 👇

{hashtags}
""",
        PostType.CAREER_UPDATE: """
{update_hook}

{story}

{reflection}

{looking_forward}

Thanks to everyone who's been part of this journey.

{hashtags}
""",
    }

    def __init__(self, project_root: str = ".") -> None:
        self.root = Path(project_root)
        self.posts_dir = self.root / "linkedin" / "posts"
        self.posts_dir.mkdir(parents=True, exist_ok=True)

        self.drafts_dir = self.posts_dir / "drafts"
        self.scheduled_dir = self.posts_dir / "scheduled"
        self.published_dir = self.posts_dir / "published"

        for d in [self.drafts_dir, self.scheduled_dir, self.published_dir]:
            d.mkdir(exist_ok=True)

        self.calendar_path = self.posts_dir / "content_calendar.json"
        self.analytics_path = self.root / "linkedin" / "analytics" / "engagement.json"

    def create_post_draft(self, post_type: PostType, **kwargs: Any) -> LinkedInPost:
        """
        Create a new post draft from template.
        """
        template = self.POST_TEMPLATES.get(post_type, "")

        # Fill template with provided kwargs
        content = template.format(**kwargs) if kwargs else template

        # Select hashtags
        hashtags = self._select_hashtags(post_type)
        content = content.replace("{hashtags}", " ".join(hashtags))

        # Create post object
        post_id = f"{post_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        post = LinkedInPost(
            id=post_id,
            type=post_type,
            title=kwargs.get("title", f"{post_type.value} post"),
            content=content.strip(),
            hashtags=hashtags,
            scheduled_date=None,
            status="draft",
            engagement=None,
            created_at=datetime.now(),
        )

        # Save draft
        self._save_post(post, self.drafts_dir)

        return post

    def _select_hashtags(self, post_type: PostType, count: int = 5) -> list[str]:
        """Select appropriate hashtags for post type."""
        hashtags = self.HASHTAG_SETS["primary"].copy()

        if post_type in [PostType.BUILD_IN_PUBLIC, PostType.CAREER_UPDATE]:
            hashtags.append("#BuildInPublic")

        if post_type in [PostType.TECHNICAL_INSIGHT, PostType.TUTORIAL]:
            hashtags.extend(random.sample(self.HASHTAG_SETS["niche"], 2))

        hashtags.extend(random.sample(self.HASHTAG_SETS["secondary"], 2))

        return list(set(hashtags))[:count]

    def _save_post(self, post: LinkedInPost, directory: Path) -> None:
        """Save post to file."""
        filepath = directory / f"{post.id}.json"
        with open(filepath, "w") as f:
            json.dump(post.to_dict(), f, indent=2)

        # Also save markdown version for easy editing
        md_path = directory / f"{post.id}.md"
        md_content = f"""# {post.title}

**Type**: {post.type.value}
**Status**: {post.status}
**Created**: {post.created_at.isoformat()}

---

{post.content}

---

**Hashtags**: {" ".join(post.hashtags)}
"""
        md_path.write_text(md_content)

    def schedule_post(self, post_id: str, scheduled_date: datetime) -> None:
        """Schedule a draft post for publishing."""
        # Find post in drafts
        draft_path = self.drafts_dir / f"{post_id}.json"

        if not draft_path.exists():
            raise FileNotFoundError(f"Post {post_id} not found in drafts")

        with open(draft_path) as f:
            data = json.load(f)

        # Update status and date
        data["status"] = "scheduled"
        data["scheduled_date"] = scheduled_date.isoformat()

        # Move to scheduled directory
        scheduled_path = self.scheduled_dir / f"{post_id}.json"
        with open(scheduled_path, "w") as f:
            json.dump(data, f, indent=2)

        # Remove from drafts
        draft_path.unlink()
        (self.drafts_dir / f"{post_id}.md").unlink(missing_ok=True)

        # Update calendar
        self._update_calendar(post_id, scheduled_date)

    def _update_calendar(self, post_id: str, scheduled_date: datetime) -> None:
        """Update content calendar."""
        calendar = self._load_calendar()

        calendar["posts"].append(
            {"id": post_id, "date": scheduled_date.isoformat(), "status": "scheduled"}
        )

        with open(self.calendar_path, "w") as f:
            json.dump(calendar, f, indent=2)

    def _load_calendar(self) -> dict[str, Any]:
        """Load content calendar."""
        if self.calendar_path.exists():
            with open(self.calendar_path) as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        return {"posts": [], "strategy": {}}

    def generate_content_calendar(self, weeks: int = 4) -> str:
        """
        Generate a content calendar for the next N weeks.
        """
        calendar = []
        start_date = datetime.now()

        # Content pillars distribution
        pillars = {
            PostType.TECHNICAL_INSIGHT: 0.4,  # 40%
            PostType.BUILD_IN_PUBLIC: 0.3,  # 30%
            PostType.INDUSTRY_COMMENTARY: 0.2,  # 20%
            PostType.CAREER_UPDATE: 0.1,  # 10%
        }

        # Schedule 2-3 posts per week
        for week in range(weeks):
            week_start = start_date + timedelta(weeks=week)
            posts_this_week = random.randint(2, 3)

            # Distribute posts across Mon, Wed, Fri
            post_days = random.sample([0, 2, 4], posts_this_week)  # Mon=0, Wed=2, Fri=4

            for day in sorted(post_days):
                post_date = week_start + timedelta(days=day - week_start.weekday())

                # Select post type based on distribution
                post_type = random.choices(list(pillars.keys()), weights=list(pillars.values()))[0]

                calendar.append(
                    {
                        "date": post_date.strftime("%Y-%m-%d"),
                        "day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][
                            post_date.weekday()
                        ],
                        "type": post_type.value,
                        "topic_suggestion": self._get_topic_suggestion(post_type),
                        "status": "planned",
                    }
                )

        # Format as table
        output = "# Content Calendar\n\n"
        output += f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n"
        output += f"Period: Next {weeks} weeks\n\n"

        output += "| Date | Day | Type | Topic Suggestion | Status |\n"
        output += "|------|-----|------|------------------|--------|\n"

        for entry in calendar:
            output += f"| {entry['date']} | {entry['day']} | {entry['type']} | {entry['topic_suggestion']} | {entry['status']} |\n"

        # Save calendar
        with open(self.calendar_path, "w") as f:
            json.dump({"posts": calendar, "generated": datetime.now().isoformat()}, f, indent=2)

        return output

    def _get_topic_suggestion(self, post_type: PostType) -> str:
        """Get topic suggestion based on post type."""
        suggestions = {
            PostType.TECHNICAL_INSIGHT: [
                "Multi-agent coordination patterns",
                "Token efficiency in LLM systems",
                "Service mesh for AI platforms",
                "RAG optimization techniques",
                "LLMOps best practices",
            ],
            PostType.BUILD_IN_PUBLIC: [
                "Project weekly update",
                "New feature implementation",
                "Architecture decision",
                "Performance optimization",
                "User feedback integration",
            ],
            PostType.INDUSTRY_COMMENTARY: [
                "Latest agent framework comparison",
                "AI infrastructure trends",
                "Production AI challenges",
                "Research paper discussion",
                "Tool/framework review",
            ],
            PostType.CAREER_UPDATE: [
                "Job search progress",
                "Skill development",
                "Milestone celebration",
                "Learning reflection",
                "Community involvement",
            ],
        }

        return random.choice(suggestions.get(post_type, ["General update"]))

    def get_post_ideas(self, post_type: PostType | None = None) -> list[str]:
        """Generate post ideas based on project and career context."""
        ideas = {
            PostType.TECHNICAL_INSIGHT: [
                "What I learned building a 27-service mesh for LLM coordination",
                "Why we achieved 32% cost reduction with intelligent provider routing",
                "The 9-layer security architecture for AI in regulated environments",
                "How A2A and MCP protocols reduced our redundant LLM calls by 45%",
                "Building evaluation frameworks with LLM-as-judge methodology",
            ],
            PostType.BUILD_IN_PUBLIC: [
                "Week N: Implementing circuit breaker patterns in the project",
                "How we scaled to 100+ concurrent agents with <150ms latency",
                "Designing the Craft API for developer experience",
                "Our journey to 116 composable patterns",
                "Building observability into multi-agent systems",
            ],
            PostType.INDUSTRY_COMMENTARY: [
                "Hot take: Most agent frameworks are solving the wrong problem",
                "Why I think multi-agent coordination will define the next AI era",
                "The hidden complexity of production LLM systems",
                "What LangChain and CrewAI get wrong about multi-agent systems",
                "The case for protocol-native agent coordination",
            ],
        }

        if post_type:
            return ideas.get(post_type, [])

        all_ideas = []
        for type_ideas in ideas.values():
            all_ideas.extend(type_ideas)
        return all_ideas

    def analyze_engagement(self) -> str:
        """Analyze post engagement and provide recommendations."""
        # Load analytics if available
        if not self.analytics_path.exists():
            return "No engagement data available yet. Start posting to collect data!"

        with open(self.analytics_path) as f:
            analytics = json.load(f)

        # Generate report
        report = "# Engagement Analysis\n\n"

        if "posts" in analytics:
            total_posts = len(analytics["posts"])
            total_likes = sum(p.get("likes", 0) for p in analytics["posts"])
            total_comments = sum(p.get("comments", 0) for p in analytics["posts"])

            report += f"**Total Posts**: {total_posts}\n"
            report += f"**Total Likes**: {total_likes}\n"
            report += f"**Total Comments**: {total_comments}\n"
            report += f"**Avg Likes/Post**: {total_likes / max(total_posts, 1):.1f}\n"
            report += f"**Avg Comments/Post**: {total_comments / max(total_posts, 1):.1f}\n"

        return report

    def suggest_headline_update(
        self,
        job_description: str,
        current_headline: str = "Building [Project] | [Role] | [Specialty]",
    ) -> dict[str, str]:
        """
        Suggest headline update based on job description.

        Args:
            job_description: Target job description
            current_headline: Current LinkedIn headline

        Returns:
            Dict with current, suggested, and reason
        """
        jd_lower = job_description.lower()

        # Check what to emphasize
        if "research" in jd_lower or "phd" in jd_lower:
            suggested = "AI Research Engineer | Multi-Agent Systems | NeurIPS 2026 Submission"
            reason = "Job emphasizes research; switching to research-focused headline"
        elif "founding" in jd_lower or "startup" in jd_lower or "0-to-1" in jd_lower:
            suggested = "AI/ML Founding Engineer | Built [Project] from 0 → production | Open to early-stage"
            reason = "Job is founding/startup role; emphasizing entrepreneurial experience"
        elif "platform" in jd_lower or "infrastructure" in jd_lower:
            suggested = (
                "AI Platform Engineer | Multi-Agent Infrastructure | 27 services, <150ms p99"
            )
            reason = "Job emphasizes platform; highlighting infrastructure experience"
        else:
            # Default: job hunting mode
            suggested = "AI Infrastructure Engineer | Building [Project] | Open to Opportunities"
            reason = "Switching to job hunting headline for visibility"

        return {"current": current_headline, "suggested": suggested, "reason": reason}

    def generate_connection_request(
        self, person_name: str, person_role: str, company: str, context: str = "recruiter"
    ) -> str:
        """
        Generate personalized connection request.

        Args:
            person_name: Name of the person
            person_role: Their role/title
            company: Their company
            context: recruiter, hiring_manager, peer

        Returns:
            Connection request message (max 300 chars)
        """
        first_name = person_name.split()[0] if person_name else "there"

        if context == "recruiter":
            message = f"""Hi {first_name},

I saw {company} is hiring for {person_role} roles. I've been building enterprise-grade AI systems and would love to learn more!

Best regards"""

        elif context == "hiring_manager":
            message = f"""Hi {first_name},

Just applied for the {person_role} role at {company}. My experience building production AI systems aligns well.

Would love to connect!"""

        else:  # peer
            message = f"""Hi {first_name},

I came across your work as {person_role} at {company} — impressive! I'm building AI coordination systems and working on similar problems.

Would love to exchange ideas!"""

        # Ensure under 300 chars
        if len(message) > 300:
            message = message[:297] + "..."

        return message

    def get_hook(self, topic: str = "multi_agent") -> str:
        """Get a random attention-grabbing hook for a topic."""
        hooks = self.HOOKS.get(topic, self.HOOKS["multi_agent"])
        return random.choice(hooks)


def main() -> None:
    """CLI for LinkedIn content management."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage LinkedIn content")
    subparsers = parser.add_subparsers(dest="command")

    # Calendar command
    cal_parser = subparsers.add_parser("calendar", help="Generate content calendar")
    cal_parser.add_argument("--weeks", type=int, default=4, help="Number of weeks")

    # Ideas command
    ideas_parser = subparsers.add_parser("ideas", help="Get post ideas")
    ideas_parser.add_argument("--type", choices=[t.value for t in PostType], help="Post type")

    # Draft command
    draft_parser = subparsers.add_parser("draft", help="Create post draft")
    draft_parser.add_argument("type", choices=[t.value for t in PostType], help="Post type")

    args = parser.parse_args()

    manager = LinkedInContentManager()

    if args.command == "calendar":
        print(manager.generate_content_calendar(args.weeks))

    elif args.command == "ideas":
        post_type = PostType(args.type) if args.type else None
        ideas = manager.get_post_ideas(post_type)
        print("# Post Ideas\n")
        for i, idea in enumerate(ideas, 1):
            print(f"{i}. {idea}")

    elif args.command == "draft":
        post_type = PostType(args.type)
        post = manager.create_post_draft(post_type)
        print(f"✅ Draft created: {post.id}")
        print(f"📁 Location: linkedin/posts/drafts/{post.id}.md")
        print("\nEdit the draft and use 'schedule' to schedule it.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
