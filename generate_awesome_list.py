#!/usr/bin/env python3
"""
Generate an organized awesome list from GitHub starred repositories.
Categorizes by use case, shows activity status, and separates inactive projects.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
import subprocess

# Category definitions with keywords for automatic classification
CATEGORIES = {
    "ai-ml": {
        "title": "🤖 AI & Machine Learning",
        "keywords": ["ai", "machine-learning", "deep-learning", "llm", "gpt", "openai", 
                     "claude", "ai-agent", "artificial-intelligence", "chatgpt", "neural",
                     "transformer", "bert", "pytorch", "tensorflow", "anthropic", "gemini"],
        "repos": []
    },
    "web-frontend": {
        "title": "🌐 Web Development - Frontend",
        "keywords": ["react", "vue", "angular", "svelte", "frontend", "nextjs", "remix",
                     "solid", "preact", "astro", "qwik", "ui", "components", "tailwindcss"],
        "repos": []
    },
    "web-fullstack": {
        "title": "🌐 Web Development - Full-Stack",
        "keywords": ["nextjs", "remix", "nuxt", "sveltekit", "full-stack", "fullstack",
                     "web-framework", "ssr", "server-side-rendering"],
        "repos": []
    },
    "backend-api": {
        "title": "⚙️ Backend & APIs",
        "keywords": ["backend", "api", "rest", "graphql", "grpc", "express", "fastapi",
                     "flask", "django", "nestjs", "fastify", "gin", "actix", "axum",
                     "database", "orm", "prisma", "drizzle", "typeorm", "authentication"],
        "repos": []
    },
    "devops": {
        "title": "🚀 DevOps & Infrastructure",
        "keywords": ["docker", "kubernetes", "k8s", "devops", "ci-cd", "deployment",
                     "infrastructure", "terraform", "ansible", "monitoring", "observability",
                     "prometheus", "grafana", "cicd", "github-actions", "gitlab-ci"],
        "repos": []
    },
    "dev-tools": {
        "title": "🛠️ Developer Tools",
        "keywords": ["cli", "terminal", "command-line", "shell", "vscode", "editor",
                     "extension", "plugin", "testing", "test", "jest", "vitest", "cypress",
                     "playwright", "git", "linter", "formatter", "prettier", "eslint"],
        "repos": []
    },
    "data-analytics": {
        "title": "📊 Data & Analytics",
        "keywords": ["data-science", "data-analysis", "visualization", "analytics",
                     "jupyter", "pandas", "numpy", "plotly", "d3", "chart", "dashboard",
                     "business-intelligence", "bi", "data-visualization"],
        "repos": []
    },
    "mobile": {
        "title": "📱 Mobile Development",
        "keywords": ["react-native", "flutter", "mobile", "ios", "android", "expo",
                     "kotlin", "swift", "mobile-app"],
        "repos": []
    },
    "design-creative": {
        "title": "🎨 Design & Creative",
        "keywords": ["design", "animation", "3d", "graphics", "svg", "canvas", "webgl",
                     "three", "threejs", "framer", "motion", "gsap", "icon", "figma"],
        "repos": []
    },
    "learning": {
        "title": "📚 Learning & Resources",
        "keywords": ["awesome", "awesome-list", "tutorial", "guide", "learning",
                     "education", "course", "book", "documentation", "cheatsheet",
                     "examples", "resources"],
        "repos": []
    },
    "security": {
        "title": "🔒 Security & Privacy",
        "keywords": ["security", "privacy", "encryption", "cryptography", "vulnerability",
                     "penetration-testing", "infosec", "cybersecurity", "auth", "oauth"],
        "repos": []
    },
    "utilities": {
        "title": "🔧 Utilities & Miscellaneous",
        "keywords": [],  # Catch-all category
        "repos": []
    }
}


def fetch_starred_repos(username: str) -> List[Dict]:
    """Fetch all starred repositories for a user using GitHub CLI."""
    print(f"Fetching starred repositories for {username}...")
    
    try:
        result = subprocess.run(
            [
                "gh", "api", "--paginate",
                f"users/{username}/starred",
                "--jq", ".[] | {name: .name, full_name: .full_name, description: .description, "
                        "language: .language, stargazers_count: .stargazers_count, "
                        "topics: .topics, pushed_at: .pushed_at, archived: .archived, "
                        "homepage: .homepage, html_url: .html_url}"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        repos = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                repos.append(json.loads(line))
        
        print(f"Fetched {len(repos)} starred repositories")
        return repos
    
    except subprocess.CalledProcessError as e:
        print(f"Error fetching repositories: {e}", file=sys.stderr)
        sys.exit(1)


def is_inactive(repo: Dict, months: int = 12) -> bool:
    """Check if a repository is inactive (no commits in specified months)."""
    if repo.get('archived'):
        return True
    
    pushed_at = repo.get('pushed_at')
    if not pushed_at:
        return True
    
    try:
        pushed_date = datetime.fromisoformat(pushed_at.replace('Z', '+00:00'))
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        return pushed_date < cutoff_date
    except (ValueError, TypeError):
        return True


def categorize_repo(repo: Dict) -> str:
    """Categorize a repository based on topics and language."""
    topics = repo.get('topics', [])
    description = (repo.get('description') or '').lower()
    language = (repo.get('language') or '').lower()
    
    # Combine all text for matching
    search_text = ' '.join(topics + [description, language])
    
    # Track category scores
    scores = defaultdict(int)
    
    for category_id, category_data in CATEGORIES.items():
        if category_id == "utilities":  # Skip catch-all
            continue
        
        for keyword in category_data['keywords']:
            if keyword in search_text:
                scores[category_id] += 1
    
    # Return category with highest score, or utilities if no match
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    return "utilities"


def format_repo_entry(repo: Dict, show_activity: bool = True) -> str:
    """Format a repository entry for the README."""
    name = repo['name']
    url = repo['html_url']
    description = (repo.get('description') or 'No description provided').strip()
    stars = repo.get('stargazers_count', 0)
    language = repo.get('language', 'Unknown')
    
    # Format last update
    activity = ""
    if show_activity and repo.get('pushed_at'):
        try:
            pushed_date = datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            days_ago = (now - pushed_date).days
            
            if days_ago < 30:
                activity = " 🔥"
            elif days_ago < 90:
                activity = " ⚡"
        except (ValueError, TypeError):
            pass
    
    # Format entry
    entry = f"- [{name}]({url})"
    if description:
        entry += f" - {description}"
    entry += f" ⭐{stars:,}"
    if language and language != "Unknown":
        entry += f" `{language}`"
    entry += activity
    
    return entry


def generate_readme(repos: List[Dict], username: str) -> str:
    """Generate the complete README content."""
    # Separate active and inactive repos
    active_repos = []
    inactive_repos = []
    
    for repo in repos:
        if is_inactive(repo):
            inactive_repos.append(repo)
        else:
            active_repos.append(repo)
    
    # Categorize active repos
    for repo in active_repos:
        category = categorize_repo(repo)
        CATEGORIES[category]['repos'].append(repo)
    
    # Sort repos within each category by stars
    for category_data in CATEGORIES.values():
        category_data['repos'].sort(key=lambda r: r.get('stargazers_count', 0), reverse=True)
    
    # Sort inactive repos by stars
    inactive_repos.sort(key=lambda r: r.get('stargazers_count', 0), reverse=True)
    
    # Generate README
    readme = []
    readme.append("# Awesome Projects [![Awesome](https://awesome.re/badge.svg)](https://github.com/sindresorhus/awesome)")
    readme.append("")
    readme.append(f"> A curated collection of {len(repos):,} starred repositories, organized by use case for the open source community.")
    readme.append("")
    readme.append(f"**Last Updated**: {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
    readme.append("")
    readme.append(f"**Stats**: {len(active_repos):,} active projects · {len(inactive_repos):,} legacy projects")
    readme.append("")
    readme.append("**Legend**: 🔥 Updated in last 30 days · ⚡ Updated in last 90 days")
    readme.append("")
    
    # Table of contents
    readme.append("## Contents")
    readme.append("")
    for category_id, category_data in CATEGORIES.items():
        if category_data['repos'] or category_id == "utilities":
            title = category_data['title']
            count = len(category_data['repos'])
            anchor = title.lower().replace(' ', '-').replace('&', '').replace('--', '-')
            # Remove emoji for anchor
            anchor = ''.join(c for c in anchor if c.isalnum() or c == '-').strip('-')
            readme.append(f"- [{title}](#-{anchor}) ({count:,})")
    
    readme.append(f"- [📦 Legacy & Inactive Projects](#-legacy--inactive-projects) ({len(inactive_repos):,})")
    readme.append("")
    readme.append("---")
    readme.append("")
    
    # Category sections
    for category_id, category_data in CATEGORIES.items():
        repos_list = category_data['repos']
        if not repos_list:
            continue
        
        readme.append(f"## {category_data['title']}")
        readme.append("")
        readme.append(f"*{len(repos_list):,} projects*")
        readme.append("")
        
        for repo in repos_list:
            readme.append(format_repo_entry(repo))
        
        readme.append("")
        readme.append("---")
        readme.append("")
    
    # Inactive section
    readme.append("## 📦 Legacy & Inactive Projects")
    readme.append("")
    readme.append(f"*{len(inactive_repos):,} projects with no commits in 12+ months or archived*")
    readme.append("")
    readme.append("<details>")
    readme.append("<summary>Show legacy projects</summary>")
    readme.append("")
    
    for repo in inactive_repos:
        readme.append(format_repo_entry(repo, show_activity=False))
    
    readme.append("")
    readme.append("</details>")
    readme.append("")
    readme.append("---")
    readme.append("")
    
    # Footer
    readme.append("## About")
    readme.append("")
    readme.append("This list is automatically generated from my starred repositories on GitHub. ")
    readme.append("The goal is to help the open source community discover great projects organized by practical use cases.")
    readme.append("")
    readme.append("**Maintained by**: [@viktorbezdek](https://github.com/viktorbezdek)")
    readme.append("")
    readme.append("**License**: [CC0 1.0 Universal](LICENSE)")
    readme.append("")
    
    return '\n'.join(readme)


def main():
    """Main execution function."""
    username = os.environ.get('GITHUB_USERNAME', 'viktorbezdek')
    
    print(f"Generating awesome list for {username}...")
    
    # Fetch repositories
    repos = fetch_starred_repos(username)
    
    # Generate README
    readme_content = generate_readme(repos, username)
    
    # Write to file
    output_file = 'README.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ Generated {output_file}")
    print(f"✓ Total repositories: {len(repos):,}")
    
    # Print category breakdown
    print("\nCategory breakdown:")
    for category_id, category_data in CATEGORIES.items():
        count = len(category_data['repos'])
        if count > 0:
            print(f"  {category_data['title']}: {count:,}")


if __name__ == '__main__':
    main()
