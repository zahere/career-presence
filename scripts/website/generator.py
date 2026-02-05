#!/usr/bin/env python3
"""
Personal Website Generator

Generates a portfolio website from master_profile.yaml.
Supports multiple static site generators: Astro, Next.js, Hugo.
"""

import yaml
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class WebsiteConfig:
    """Website generation configuration"""
    generator: str  # astro, nextjs, hugo
    theme: str
    domain: str
    output_dir: str
    sections: List[str]


class WebsiteGenerator:
    """
    Generates portfolio website from master profile data.
    """
    
    GENERATORS = {
        'astro': {
            'init_cmd': 'npm create astro@latest {output_dir} -- --template minimal',
            'build_cmd': 'npm run build',
            'dev_cmd': 'npm run dev',
            'content_dir': 'src/content',
            'pages_dir': 'src/pages',
        },
        'nextjs': {
            'init_cmd': 'npx create-next-app@latest {output_dir} --typescript --tailwind --app',
            'build_cmd': 'npm run build',
            'dev_cmd': 'npm run dev',
            'content_dir': 'content',
            'pages_dir': 'app',
        },
        'hugo': {
            'init_cmd': 'hugo new site {output_dir}',
            'build_cmd': 'hugo',
            'dev_cmd': 'hugo server',
            'content_dir': 'content',
            'pages_dir': 'layouts',
        }
    }
    
    def __init__(self, profile_path: str, output_dir: str = 'website'):
        """
        Initialize generator.
        
        Args:
            profile_path: Path to master_profile.yaml
            output_dir: Where to generate the website
        """
        with open(profile_path) as f:
            self.profile = yaml.safe_load(f)
        
        self.output_dir = Path(output_dir)
        self.generator = 'astro'  # Default
        
    def generate_homepage_content(self) -> str:
        """Generate homepage markdown/MDX content."""
        personal = self.profile['personal']
        summary = self.profile['summaries']['website']
        
        return f"""---
title: "{personal['name']['full']}"
description: "{personal['tagline']}"
---

# {personal['name']['full']}

## {personal['headlines']['website']}

{summary}

## What I Do

I specialize in building production-grade AI systems that bridge the gap between cutting-edge research and real-world deployment.

### Current Focus
- Building **AgentiCraft** - Enterprise multi-agent coordination platform
- Researching token efficiency in multi-agent LLM coordination
- Exploring protocol-native MCP and A2A integration

[View My Projects](/projects) · [Download Resume](/resume.pdf) · [Get In Touch](/contact)
"""

    def generate_about_page(self) -> str:
        """Generate about page content."""
        personal = self.profile['personal']
        summary = self.profile['summaries']['website']
        education = self.profile['education']
        
        edu_section = "\n".join([
            f"- **{edu['degree']}** - {edu['institution']} ({edu.get('start_date', '')} - {edu.get('end_date', 'Present')})"
            for edu in education
        ])
        
        return f"""---
title: "About Me"
description: "Learn more about {personal['name']['full']}"
---

# About Me

{summary}

## Background

{personal['name']['first']} is an AI Infrastructure Engineer based in {personal['contact']['location']}.

## Education

{edu_section}

## Languages

{', '.join([f"{lang['language']} ({lang['proficiency']})" for lang in personal['languages']])}

## Connect

- **Email**: {personal['contact']['email']}
- **LinkedIn**: [{personal['social']['linkedin']}]({personal['social']['linkedin']})
- **GitHub**: [{personal['social']['github']}]({personal['social']['github']})
"""

    def generate_projects_page(self) -> str:
        """Generate projects showcase page."""
        projects = self.profile.get('projects', [])
        
        project_cards = []
        for project in projects:
            highlights = "\n".join([f"  - {h}" for h in project.get('highlights', [])])
            tech = ", ".join(project.get('technologies', []))
            
            card = f"""
### {project['name']}

**{project['tagline']}**

{project['description']}

**Highlights:**
{highlights}

**Tech Stack:** {tech}

[View Repository]({project.get('repo_url', '#')})

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
        experiences = self.profile.get('experience', [])
        
        exp_sections = []
        for exp in experiences:
            bullets = "\n".join([f"- {b['text']}" for b in exp.get('bullets', [])])
            end_date = exp.get('end_date') or 'Present'
            
            section = f"""
## {exp['company']}

**{exp['role']}** | {exp.get('location', 'Remote')} | {exp['start_date']} - {end_date}

{exp.get('short_description', '')}

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
        skills = self.profile.get('skills', {}).get('categories', [])
        
        skill_sections = []
        for category in skills:
            skill_list = ", ".join([s['name'] for s in category.get('skills', [])])
            skill_sections.append(f"""
### {category['name']}

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
        personal = self.profile['personal']
        
        return f"""---
title: "Contact"
description: "Get in touch"
---

# Get In Touch

I'm always interested in hearing about new opportunities, collaborations, or just connecting with fellow builders in the AI space.

## Reach Out

- **Email**: [{personal['contact']['email']}](mailto:{personal['contact']['email']})
- **LinkedIn**: [{personal['social']['linkedin'].split('/')[-1]}]({personal['social']['linkedin']})
- **GitHub**: [@{personal['social']['github'].split('/')[-1]}]({personal['social']['github']})

## Location

Based in {personal['contact']['location']} ({personal['contact']['timezone']})

Open to remote opportunities worldwide.

---

*Response time: Usually within 24-48 hours*
"""

    def generate_blog_index(self) -> str:
        """Generate blog index page."""
        return """---
title: "Blog"
description: "Technical writing and thoughts"
---

# Blog

Thoughts on AI infrastructure, multi-agent systems, and building production-ready AI.

## Recent Posts

*Coming soon...*

---

## Topics I Write About

- Multi-agent coordination patterns
- Production LLM systems
- MLOps and infrastructure
- Building AgentiCraft
- Career in AI engineering
"""

    def generate_astro_config(self) -> str:
        """Generate Astro configuration file."""
        return """import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';

export default defineConfig({
  site: 'https://yourwebsite.com',
  integrations: [tailwind(), mdx()],
  markdown: {
    shikiConfig: {
      theme: 'github-dark',
    },
  },
});
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
        personal = self.profile['personal']
        
        return f"""---
interface Props {{
  title: string;
  description?: string;
}}

const {{ title, description = "{personal['tagline']}" }} = Astro.props;
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content={{description}} />
    <title>{{title}} | {personal['name']['full']}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet" />
  </head>
  <body class="bg-gray-900 text-gray-100 min-h-screen">
    <nav class="fixed top-0 w-full bg-gray-900/80 backdrop-blur-sm border-b border-gray-800 z-50">
      <div class="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
        <a href="/" class="font-bold text-xl">{personal['name']['first']}</a>
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
        <p>&copy; {{new Date().getFullYear()}} {personal['name']['full']}. Built with Astro.</p>
        <div class="mt-4 flex justify-center gap-4">
          <a href="{personal['social']['linkedin']}" class="hover:text-primary">LinkedIn</a>
          <a href="{personal['social']['github']}" class="hover:text-primary">GitHub</a>
          <a href="mailto:{personal['contact']['email']}" class="hover:text-primary">Email</a>
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

    def generate_all(self):
        """Generate complete website structure."""
        # Create directories
        dirs = [
            self.output_dir / 'src' / 'pages',
            self.output_dir / 'src' / 'layouts',
            self.output_dir / 'src' / 'content' / 'blog',
            self.output_dir / 'public',
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        
        # Generate configuration files
        (self.output_dir / 'astro.config.mjs').write_text(self.generate_astro_config())
        (self.output_dir / 'tailwind.config.mjs').write_text(self.generate_tailwind_config())
        
        # Generate layout
        (self.output_dir / 'src' / 'layouts' / 'Layout.astro').write_text(
            self.generate_layout_component()
        )
        
        # Generate pages
        pages = {
            'index': ('Home', self.generate_homepage_content()),
            'about': ('About', self.generate_about_page()),
            'projects': ('Projects', self.generate_projects_page()),
            'experience': ('Experience', self.generate_experience_page()),
            'skills': ('Skills', self.generate_skills_page()),
            'contact': ('Contact', self.generate_contact_page()),
            'blog': ('Blog', self.generate_blog_index()),
        }
        
        for page_name, (title, content) in pages.items():
            # Save as markdown in content directory
            content_path = self.output_dir / 'src' / 'content' / f'{page_name}.md'
            content_path.write_text(content)
        
        # Generate package.json
        package_json = {
            "name": "portfolio-website",
            "type": "module",
            "version": "1.0.0",
            "scripts": {
                "dev": "astro dev",
                "build": "astro build",
                "preview": "astro preview"
            },
            "dependencies": {
                "astro": "^4.0.0",
                "@astrojs/tailwind": "^5.0.0",
                "@astrojs/mdx": "^2.0.0",
                "tailwindcss": "^3.4.0"
            }
        }
        
        (self.output_dir / 'package.json').write_text(
            json.dumps(package_json, indent=2)
        )
        
        print(f"✅ Website generated in {self.output_dir}")
        print(f"\nNext steps:")
        print(f"  cd {self.output_dir}")
        print(f"  npm install")
        print(f"  npm run dev")
        
        return self.output_dir


def main():
    """Generate website from profile."""
    generator = WebsiteGenerator(
        profile_path='config/master_profile.yaml',
        output_dir='website'
    )
    generator.generate_all()


if __name__ == '__main__':
    main()
