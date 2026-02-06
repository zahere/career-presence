#!/usr/bin/env python3
"""
Personal Website Generator

Generates a portfolio website from master_profile.yaml.
Supports multiple static site generators: Astro, Next.js, Hugo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class WebsiteConfig:
    """Website generation configuration"""

    generator: str  # astro, nextjs, hugo
    theme: str
    domain: str
    output_dir: str
    sections: list[str]


class WebsiteGenerator:
    """
    Generates portfolio website from master profile data.
    """

    GENERATORS = {
        "astro": {
            "init_cmd": "npm create astro@latest {output_dir} -- --template minimal",
            "build_cmd": "npm run build",
            "dev_cmd": "npm run dev",
            "content_dir": "src/content",
            "pages_dir": "src/pages",
        },
        "nextjs": {
            "init_cmd": "npx create-next-app@latest {output_dir} --typescript --tailwind --app",
            "build_cmd": "npm run build",
            "dev_cmd": "npm run dev",
            "content_dir": "content",
            "pages_dir": "app",
        },
        "hugo": {
            "init_cmd": "hugo new site {output_dir}",
            "build_cmd": "hugo",
            "dev_cmd": "hugo server",
            "content_dir": "content",
            "pages_dir": "layouts",
        },
    }

    def __init__(self, profile_path: str, output_dir: str = "website") -> None:
        """
        Initialize generator.

        Args:
            profile_path: Path to master_profile.yaml
            output_dir: Where to generate the website
        """
        with open(profile_path) as f:
            self.profile = yaml.safe_load(f)

        self.output_dir = Path(output_dir)
        self.generator = "astro"  # Default

    def _get_website_content(self, key: str, default: str = "") -> str:
        """Get a value from the website_content profile section."""
        value: str = self.profile.get("website_content", {}).get(key, default)
        return value

    def _format_current_focus(self) -> str:
        """Format current focus items as markdown list."""
        items = self.profile.get("website_content", {}).get("current_focus", [])
        if not items:
            return "- Working on exciting projects"
        return "\n".join(f"- {item}" for item in items)

    def generate_homepage_content(self) -> str:
        """Generate homepage markdown/MDX content."""
        personal = self.profile["personal"]
        summary = self.profile["summaries"]["website"]

        return f"""---
title: "{personal["name"]["full"]}"
description: "{personal["tagline"]}"
---

# {personal["name"]["full"]}

## {personal["headlines"]["website"]}

{summary}

## What I Do

{self._get_website_content("what_i_do", "I specialize in building production-grade AI systems.")}

### Current Focus
{self._format_current_focus()}

[View My Projects](/projects) · [Download Resume](/resume.pdf) · [Get In Touch](/contact)
"""

    def generate_about_page(self) -> str:
        """Generate about page content."""
        personal = self.profile["personal"]
        summary = self.profile["summaries"]["website"]
        education = self.profile["education"]

        edu_section = "\n".join(
            [
                f"- **{edu['degree']}** - {edu['institution']} ({edu.get('start_date', '')} - {edu.get('end_date', 'Present')})"
                for edu in education
            ]
        )

        return f"""---
title: "About Me"
description: "Learn more about {personal["name"]["full"]}"
---

# About Me

{summary}

## Background

{personal["name"]["first"]} is {personal["headlines"].get("about", personal["headlines"]["website"])} based in {personal["contact"]["location"]}.

## Education

{edu_section}

## Languages

{", ".join([f"{lang['language']} ({lang['proficiency']})" for lang in personal["languages"]])}

## Connect

- **Email**: {personal["contact"]["email"]}
- **LinkedIn**: [{personal["social"]["linkedin"]}]({personal["social"]["linkedin"]})
- **GitHub**: [{personal["social"]["github"]}]({personal["social"]["github"]})
"""

    def generate_projects_page(self) -> str:
        """Generate projects showcase page."""
        projects = self.profile.get("projects", [])

        project_cards = []
        for project in projects:
            highlights = "\n".join([f"  - {h}" for h in project.get("highlights", [])])
            tech = ", ".join(project.get("technologies", []))

            card = f"""
### {project["name"]}

**{project["tagline"]}**

{project["description"]}

**Highlights:**
{highlights}

**Tech Stack:** {tech}

[View Repository]({project.get("repo_url", "#")})

---
"""
            project_cards.append(card)

        return f"""---
title: "Projects"
description: "Featured projects and work"
---

# Projects

{"".join(project_cards)}
"""

    def generate_experience_page(self) -> str:
        """Generate experience/resume page."""
        experiences = self.profile.get("experience", [])

        exp_sections = []
        for exp in experiences:
            bullets = "\n".join([f"- {b['text']}" for b in exp.get("bullets", [])])
            end_date = exp.get("end_date") or "Present"

            section = f"""
## {exp["company"]}

**{exp["role"]}** | {exp.get("location", "Remote")} | {exp["start_date"]} - {end_date}

{exp.get("short_description", "")}

{bullets}

---
"""
            exp_sections.append(section)

        return f"""---
title: "Experience"
description: "Professional experience and work history"
---

# Experience

{"".join(exp_sections)}

[Download Full Resume (PDF)](/resume.pdf)
"""

    def generate_skills_page(self) -> str:
        """Generate skills page with visual representation."""
        skills = self.profile.get("skills", {}).get("categories", [])

        skill_sections = []
        for category in skills:
            skill_list = ", ".join([s["name"] for s in category.get("skills", [])])
            skill_sections.append(f"""
### {category["name"]}

{skill_list}
""")

        return f"""---
title: "Skills"
description: "Technical skills and expertise"
---

# Technical Skills

{"".join(skill_sections)}
"""

    def generate_contact_page(self) -> str:
        """Generate contact page."""
        personal = self.profile["personal"]

        return f"""---
title: "Contact"
description: "Get in touch"
---

# Get In Touch

{self._get_website_content("contact_intro", "I'm always interested in hearing about new opportunities and collaborations.")}

## Reach Out

- **Email**: [{personal["contact"]["email"]}](mailto:{personal["contact"]["email"]})
- **LinkedIn**: [{personal["social"]["linkedin"].split("/")[-1]}]({personal["social"]["linkedin"]})
- **GitHub**: [@{personal["social"]["github"].split("/")[-1]}]({personal["social"]["github"]})

## Location

Based in {personal["contact"]["location"]} ({personal["contact"]["timezone"]})

{self._get_website_content("location_openness", "Open to remote opportunities worldwide.")}

---

*Response time: Usually within 24-48 hours*
"""

    def generate_blog_index(self) -> str:
        """Generate blog index page."""
        blog_description = self._get_website_content(
            "blog_description", "Technical writing and thoughts."
        )
        blog_topics = self.profile.get("website_content", {}).get("blog_topics", [])
        if not blog_topics:
            blog_topics = [
                "Technical topics",
                "Industry insights",
                "Career reflections",
            ]
        topics_list = "\n".join(f"- {topic}" for topic in blog_topics)

        return f"""---
title: "Blog"
description: "Technical writing and thoughts"
---

# Blog

{blog_description}

## Recent Posts

*Coming soon...*

---

## Topics I Write About

{topics_list}
"""

    def generate_astro_config(self) -> str:
        """Generate Astro configuration file."""
        domain = self.profile.get("personal", {}).get("social", {}).get(
            "website", ""
        ) or self.profile.get("website", {}).get("domain", "")
        site_url = (
            domain
            if domain.startswith("http")
            else f"https://{domain}"
            if domain
            else "https://yourwebsite.com"
        )
        return f"""import {{ defineConfig }} from 'astro/config';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';

export default defineConfig({{
  site: '{site_url}',
  integrations: [tailwind(), mdx()],
  markdown: {{
    shikiConfig: {{
      theme: 'github-dark',
    }},
  }},
}});
"""

    def generate_tailwind_config(self) -> str:
        """Generate Tailwind CSS configuration."""
        return """/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        secondary: '#10B981',
        accent: '#8B5CF6',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
"""

    def generate_layout_component(self) -> str:
        """Generate main layout component for Astro."""
        personal = self.profile["personal"]

        return f"""---
interface Props {{
  title: string;
  description?: string;
}}

const {{ title, description = "{personal["tagline"]}" }} = Astro.props;
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content={{description}} />
    <title>{{title}} | {personal["name"]["full"]}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet" />
  </head>
  <body class="bg-gray-900 text-gray-100 min-h-screen">
    <nav class="fixed top-0 w-full bg-gray-900/80 backdrop-blur-sm border-b border-gray-800 z-50">
      <div class="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
        <a href="/" class="font-bold text-xl">{personal["name"]["first"]}</a>
        <div class="flex gap-6">
          <a href="/about" class="hover:text-primary transition">About</a>
          <a href="/projects" class="hover:text-primary transition">Projects</a>
          <a href="/experience" class="hover:text-primary transition">Experience</a>
          <a href="/blog" class="hover:text-primary transition">Blog</a>
          <a href="/contact" class="hover:text-primary transition">Contact</a>
        </div>
      </div>
    </nav>

    <main class="max-w-4xl mx-auto px-4 pt-24 pb-16">
      <slot />
    </main>

    <footer class="border-t border-gray-800 py-8">
      <div class="max-w-4xl mx-auto px-4 text-center text-gray-500">
        <p>&copy; {{new Date().getFullYear()}} {personal["name"]["full"]}. Built with Astro.</p>
        <div class="mt-4 flex justify-center gap-4">
          <a href="{personal["social"]["linkedin"]}" class="hover:text-primary">LinkedIn</a>
          <a href="{personal["social"]["github"]}" class="hover:text-primary">GitHub</a>
          <a href="mailto:{personal["contact"]["email"]}" class="hover:text-primary">Email</a>
        </div>
      </div>
    </footer>
  </body>
</html>

<style is:global>
  @tailwind base;
  @tailwind components;
  @tailwind utilities;

  .prose {{
    @apply text-gray-300 leading-relaxed;
  }}

  .prose h1 {{
    @apply text-4xl font-bold text-white mb-6;
  }}

  .prose h2 {{
    @apply text-2xl font-semibold text-white mt-8 mb-4;
  }}

  .prose h3 {{
    @apply text-xl font-semibold text-white mt-6 mb-3;
  }}

  .prose a {{
    @apply text-primary hover:underline;
  }}

  .prose code {{
    @apply bg-gray-800 px-1.5 py-0.5 rounded text-sm font-mono;
  }}

  .prose pre {{
    @apply bg-gray-800 p-4 rounded-lg overflow-x-auto;
  }}

  .prose ul {{
    @apply list-disc list-inside space-y-2 my-4;
  }}
</style>
"""

    def generate_page_template(self, title: str, content: str) -> str:
        """Generate an Astro page from content."""
        return f"""---
import Layout from '../layouts/Layout.astro';
---

<Layout title="{title}">
  <article class="prose max-w-none">
    {content}
  </article>
</Layout>
"""

    def _generate_site_config(self) -> str:
        """Generate site.config.ts with personal data (gitignored)."""
        personal = self.profile["personal"]
        return f"""// Auto-generated from master_profile.yaml — DO NOT commit this file
export const siteConfig = {{
  name: "{personal["name"]["full"]}",
  shortName: "{personal["name"]["first"]}",
  tagline: "{personal["tagline"]}",
  social: {{
    linkedin: "{personal["social"]["linkedin"]}",
    github: "{personal["social"]["github"]}",
    email: "{personal["contact"]["email"]}",
  }},
}};
"""

    def generate_all(self) -> Path:
        """Generate complete website structure."""
        # Create directories
        dirs = [
            self.output_dir / "src" / "pages",
            self.output_dir / "src" / "layouts",
            self.output_dir / "src" / "config",
            self.output_dir / "src" / "content" / "pages",
            self.output_dir / "src" / "content" / "blog",
            self.output_dir / "public",
        ]

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        # Generate site config with personal data (gitignored)
        (self.output_dir / "src" / "config" / "site.config.ts").write_text(
            self._generate_site_config()
        )

        # Only write scaffold files if they don't already exist (avoid overwriting tracked files)
        scaffold_files = {
            self.output_dir / "astro.config.mjs": self.generate_astro_config,
            self.output_dir / "tailwind.config.mjs": self.generate_tailwind_config,
            self.output_dir / "src" / "layouts" / "Layout.astro": self.generate_layout_component,
        }

        for path, generator in scaffold_files.items():
            if not path.exists():
                path.write_text(generator())

        # Generate pages (content directory is gitignored)
        pages = {
            "index": ("Home", self.generate_homepage_content()),
            "about": ("About", self.generate_about_page()),
            "projects": ("Projects", self.generate_projects_page()),
            "experience": ("Experience", self.generate_experience_page()),
            "skills": ("Skills", self.generate_skills_page()),
            "contact": ("Contact", self.generate_contact_page()),
            "blog": ("Blog", self.generate_blog_index()),
        }

        for page_name, (_title, content) in pages.items():
            content_path = self.output_dir / "src" / "content" / "pages" / f"{page_name}.md"
            content_path.write_text(content)

        # Only write package.json if it doesn't exist
        package_path = self.output_dir / "package.json"
        if not package_path.exists():
            package_json = {
                "name": "portfolio-website",
                "type": "module",
                "version": "1.0.0",
                "scripts": {
                    "dev": "astro dev",
                    "build": "astro build",
                    "preview": "astro preview",
                },
                "dependencies": {
                    "astro": "^4.0.0",
                    "@astrojs/tailwind": "^5.0.0",
                    "@astrojs/mdx": "^2.0.0",
                    "tailwindcss": "^3.4.0",
                },
            }
            package_path.write_text(json.dumps(package_json, indent=2))

        print(f"✅ Website generated in {self.output_dir}")
        print("\nNext steps:")
        print(f"  cd {self.output_dir}")
        print("  npm install")
        print("  npm run dev")

        return self.output_dir


def main() -> None:
    """Generate website from profile."""
    generator = WebsiteGenerator(profile_path="config/master_profile.yaml", output_dir="website")
    generator.generate_all()


if __name__ == "__main__":
    main()
