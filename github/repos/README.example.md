# GitHub Repos Directory

This directory contains README templates for your GitHub repositories.

## Structure

```
github/repos/
├── project-name/
│   └── README.md      # Generated from master_profile.yaml
└── another-project/
    └── README.md
```

## Project README Template

Each project README should follow this structure:

```markdown
# Project Name

Brief project description

## Overview

Detailed overview of your project, its purpose, and key features.

## Highlights

- Key feature 1
- Key feature 2
- Key metric or achievement

## Tech Stack

Technologies used in this project

## Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/username/project
cd project

# Install dependencies
pip install -r requirements.txt
\`\`\`

## Usage

\`\`\`python
# Quick start example
from project import main

main()
\`\`\`

## Documentation

See [docs/](./docs/) for full documentation.

## License

Your license - see [LICENSE](./LICENSE) for details.

---

Built by [Your Name](https://github.com/username)
```

## Usage

Run `/sync github` to generate READMEs from your master_profile.yaml projects.
