#!/usr/bin/env python3
"""
Kalybrate Skill Discovery - Two-Phase Approach

Phase 1: Get skill list (from Playwright scrape OR fallback data with known repos)
Phase 2: Fetch SKILL.md directly from GitHub raw URLs (no JavaScript needed!)

The key insight: SkillsMP is just a directory. The actual SKILL.md files live on GitHub.
We do NOT need to scrape SkillsMP detail pages - just get repo URLs and fetch from GitHub.
"""

import json
import time
import re
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class DiscoveredSkill:
    """A skill discovered from SkillsMP"""
    name: str
    repository: str  # e.g., "pytorch/pytorch"
    stars: int = 0
    stars_display: str = ""
    skillsmp_url: str = ""
    description: str = ""
    rank: int = 0
    category: str = ""

    # Populated after GitHub fetch
    skill_md_content: Optional[str] = None
    skill_md_url: Optional[str] = None
    github_stars: Optional[int] = None
    last_updated: Optional[str] = None

    # Status
    fetch_status: str = "pending"  # pending, success, not_found, error


class SkillDiscovery:
    """
    Two-phase skill discovery:
    1. Get skill list from SkillsMP (via Playwright scrape or fallback data)
    2. Fetch SKILL.md from GitHub raw URLs (simple HTTP, no JS needed!)
    """

    GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
    GITHUB_API_BASE = "https://api.github.com"

    def __init__(self, github_token: Optional[str] = None, delay: float = 0.5):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Kalybrate-Skill-Discovery/1.0',
            'Accept': 'text/plain',
        })
        if github_token:
            self.session.headers['Authorization'] = f'token {github_token}'

    def get_curated_skills(self) -> Tuple[List[DiscoveredSkill], Dict[str, str]]:
        """
        Return curated skill data from real SkillsMP listings.
        Includes the known GitHub paths where SKILL.md files live.

        Returns:
            - List of DiscoveredSkill objects
            - Dict mapping skill name to known SKILL.md path in repo
        """
        # Real skills from SkillsMP with their actual GitHub paths
        skills_data = [
            # PyTorch skills (95.4k stars) - path: .claude/skills/{name}/SKILL.md
            {
                "name": "skill-writer",
                "repository": "pytorch/pytorch",
                "stars": 95362,
                "stars_display": "95.4k",
                "description": "Guide users through creating Agent Skills for Claude Code",
                "category": "tools",
                "skill_path": ".claude/skills/skill-writer/SKILL.md",
            },
            {
                "name": "docstring",
                "repository": "pytorch/pytorch",
                "stars": 95362,
                "stars_display": "95.4k",
                "description": "Write docstrings for PyTorch functions and methods",
                "category": "documentation",
                "skill_path": ".claude/skills/docstring/SKILL.md",
            },
            {
                "name": "at-dispatch-v2",
                "repository": "pytorch/pytorch",
                "stars": 95362,
                "stars_display": "95.4k",
                "description": "Convert PyTorch AT_DISPATCH macros to AT_DISPATCH_V2",
                "category": "development",
                "skill_path": ".claude/skills/at-dispatch-v2/SKILL.md",
            },
            {
                "name": "add-uint-support",
                "repository": "pytorch/pytorch",
                "stars": 95362,
                "stars_display": "95.4k",
                "description": "Add unsigned integer type support to PyTorch operators",
                "category": "development",
                "skill_path": ".claude/skills/add-uint-support/SKILL.md",
            },
            # Anthropic Claude Code skills (47.9k stars)
            {
                "name": "frontend-design",
                "repository": "anthropics/claude-code",
                "stars": 47860,
                "stars_display": "47.9k",
                "description": "Create distinctive, production-grade frontend interfaces",
                "category": "tools",
                "skill_path": "plugins/frontend-design/skills/frontend-design/SKILL.md",
            },
            {
                "name": "hook-development",
                "repository": "anthropics/claude-code",
                "stars": 47860,
                "stars_display": "47.9k",
                "description": "Create hooks for Claude Code plugins",
                "category": "tools",
                "skill_path": "plugins/plugin-dev/skills/hook-development/SKILL.md",
            },
            {
                "name": "command-development",
                "repository": "anthropics/claude-code",
                "stars": 47860,
                "stars_display": "47.9k",
                "description": "Create slash commands for Claude Code",
                "category": "tools",
                "skill_path": "plugins/plugin-dev/skills/command-development/SKILL.md",
            },
            {
                "name": "mcp-integration",
                "repository": "anthropics/claude-code",
                "stars": 47860,
                "stars_display": "47.9k",
                "description": "Integrate MCP servers with Claude Code plugins",
                "category": "tools",
                "skill_path": "plugins/plugin-dev/skills/mcp-integration/SKILL.md",
            },
            {
                "name": "agent-development",
                "repository": "anthropics/claude-code",
                "stars": 47860,
                "stars_display": "47.9k",
                "description": "Create custom agents for Claude Code",
                "category": "tools",
                "skill_path": "plugins/plugin-dev/skills/agent-development/SKILL.md",
            },
            {
                "name": "writing-rules",
                "repository": "anthropics/claude-code",
                "stars": 47860,
                "stars_display": "47.9k",
                "description": "Write hookify rules for Claude Code",
                "category": "tools",
                "skill_path": "plugins/hookify/skills/writing-rules/SKILL.md",
            },
            # Metabase skills (44.7k stars)
            {
                "name": "typescript-review",
                "repository": "metabase/metabase",
                "stars": 44733,
                "stars_display": "44.7k",
                "description": "Review TypeScript code for quality and best practices",
                "category": "development",
                "skill_path": ".claude/skills/typescript-review/SKILL.md",
            },
            {
                "name": "typescript-write",
                "repository": "metabase/metabase",
                "stars": 44733,
                "stars_display": "44.7k",
                "description": "Write TypeScript code following Metabase conventions",
                "category": "development",
                "skill_path": ".claude/skills/typescript-write/SKILL.md",
            },
            {
                "name": "clojure-write",
                "repository": "metabase/metabase",
                "stars": 44733,
                "stars_display": "44.7k",
                "description": "Write Clojure code following Metabase conventions",
                "category": "development",
                "skill_path": ".claude/skills/clojure-write/SKILL.md",
            },
            # OpenAI Codex skills (54.7k stars)
            {
                "name": "skill-creator",
                "repository": "openai/codex",
                "stars": 54700,
                "stars_display": "54.7k",
                "description": "Guide for creating effective Codex skills",
                "category": "tools",
                "skill_path": "codex-cli/skills/skill-creator/SKILL.md",
            },
            {
                "name": "skill-installer",
                "repository": "openai/codex",
                "stars": 54700,
                "stars_display": "54.7k",
                "description": "Install Codex skills from curated list or GitHub",
                "category": "tools",
                "skill_path": "codex-cli/skills/skill-installer/SKILL.md",
            },
            # Anthropic official skills repo
            {
                "name": "pdf",
                "repository": "anthropics/skills",
                "stars": 15000,
                "stars_display": "15k",
                "description": "Create, read, and manipulate PDF documents",
                "category": "tools",
                "skill_path": "skills/pdf/SKILL.md",
            },
            {
                "name": "ms-office-suite",
                "repository": "anthropics/skills",
                "stars": 15000,
                "stars_display": "15k",
                "description": "Create Microsoft Office files (Excel, Word, PowerPoint)",
                "category": "tools",
                "skill_path": "skills/ms-office-suite/SKILL.md",
            },
        ]

        # Build DiscoveredSkill objects
        skills = []
        skill_paths = {}

        for i, s in enumerate(skills_data, 1):
            skill = DiscoveredSkill(
                name=s["name"],
                repository=s["repository"],
                stars=s["stars"],
                stars_display=s["stars_display"],
                description=s["description"],
                category=s.get("category", ""),
                rank=i,
                skillsmp_url=f"https://skillsmp.com/skills/{s['name']}",
            )
            skills.append(skill)
            skill_paths[s["name"]] = s.get("skill_path", "")

        return skills, skill_paths

    def fetch_skill_md(self, skill: DiscoveredSkill, known_path: Optional[str] = None) -> bool:
        """
        Fetch SKILL.md content directly from GitHub raw URL.

        This is the key insight: We fetch directly from GitHub, NOT from SkillsMP.
        GitHub raw files are just text - no JavaScript needed!

        Args:
            skill: The skill to fetch
            known_path: If we know the exact path in the repo, try it first

        Returns:
            True if successful
        """
        print(f"  📄 Fetching SKILL.md for: {skill.name} ({skill.repository})")

        # Build list of paths to try
        paths_to_try = []

        # If we have a known path, try it first
        if known_path:
            paths_to_try.append(known_path)

        # Add common path patterns
        common_paths = [
            f".claude/skills/{skill.name}/SKILL.md",
            f"skills/{skill.name}/SKILL.md",
            "SKILL.md",
            ".claude/skills/SKILL.md",
            "skills/SKILL.md",
            "skill/SKILL.md",
        ]

        for path in common_paths:
            if path not in paths_to_try:
                paths_to_try.append(path)

        # Try each path with each branch
        for path in paths_to_try:
            for branch in ['main', 'master']:
                url = f"{self.GITHUB_RAW_BASE}/{skill.repository}/{branch}/{path}"

                try:
                    response = self.session.get(url, timeout=10)

                    if response.status_code == 200:
                        content = response.text

                        # Validate it looks like a SKILL.md
                        if self._is_valid_skill_md(content):
                            skill.skill_md_content = content
                            skill.skill_md_url = url
                            skill.fetch_status = "success"
                            print(f"    ✅ Found: {path} ({len(content):,} chars)")
                            return True

                except requests.RequestException:
                    continue

        skill.fetch_status = "not_found"
        print(f"    ❌ SKILL.md not found")
        return False

    def _is_valid_skill_md(self, content: str) -> bool:
        """Check if content looks like a valid SKILL.md"""
        if len(content) < 50:
            return False

        # Should have YAML frontmatter
        has_frontmatter = content.strip().startswith('---')
        # Or markdown headers
        has_headers = '#' in content
        # Or skill-related keywords
        has_keywords = any(kw in content.lower() for kw in
            ['instruction', 'step', 'usage', 'example', 'description', 'skill'])

        return has_frontmatter or (has_headers and has_keywords)

    def fetch_github_metadata(self, skill: DiscoveredSkill) -> bool:
        """Fetch additional metadata from GitHub API"""
        url = f"{self.GITHUB_API_BASE}/repos/{skill.repository}"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                skill.github_stars = data.get('stargazers_count', 0)
                skill.last_updated = data.get('pushed_at', '')
                return True
        except Exception:
            pass

        return False

    def discover_skills(self, limit: int = 20) -> List[DiscoveredSkill]:
        """
        Full discovery flow:
        1. Get skill list from curated data (real SkillsMP skills)
        2. Fetch SKILL.md from GitHub for each (simple HTTP requests!)
        3. Get GitHub metadata
        """

        print("=" * 60)
        print("🔍 PHASE 1: Loading skill list from curated data")
        print("=" * 60)

        skills, skill_paths = self.get_curated_skills()
        skills = skills[:limit]

        print(f"📊 Loaded {len(skills)} skills")
        for skill in skills[:5]:
            print(f"  - {skill.name} ({skill.repository})")
        if len(skills) > 5:
            print(f"  ... and {len(skills) - 5} more")

        print("\n" + "=" * 60)
        print("📥 PHASE 2: Fetching SKILL.md from GitHub")
        print("=" * 60)

        success_count = 0
        for skill in skills:
            known_path = skill_paths.get(skill.name)
            if self.fetch_skill_md(skill, known_path):
                success_count += 1
                self.fetch_github_metadata(skill)
            time.sleep(self.delay)

        print(f"\n📊 Results: {success_count}/{len(skills)} skills fetched successfully")

        return skills

    def save_results(self, skills: List[DiscoveredSkill], output_path: str):
        """Save discovered skills to JSON and individual files"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON
        skills_data = [asdict(skill) for skill in skills]

        data = {
            'discovered_at': datetime.utcnow().isoformat(),
            'source': 'skillsmp.com + github.com',
            'total_discovered': len(skills),
            'successfully_fetched': len([s for s in skills if s.fetch_status == 'success']),
            'skills': skills_data,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n✅ Saved to {output_file}")

        # Save individual SKILL.md files
        skills_dir = output_file.parent / 'skills'
        skills_dir.mkdir(exist_ok=True)

        for skill in skills:
            if skill.skill_md_content:
                skill_dir = skills_dir / skill.name
                skill_dir.mkdir(exist_ok=True)

                # Save SKILL.md
                (skill_dir / 'SKILL.md').write_text(skill.skill_md_content)

                # Save metadata
                meta = asdict(skill)
                del meta['skill_md_content']  # Don't duplicate the content
                (skill_dir / 'metadata.json').write_text(json.dumps(meta, indent=2))

        print(f"📁 Individual SKILL.md files saved to {skills_dir}/")


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Discover skills from SkillsMP + GitHub')
    parser.add_argument('--limit', type=int, default=20, help='Max skills to fetch')
    parser.add_argument('--output', type=str, default='data/discovered/skills.json')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests')

    args = parser.parse_args()

    # Get GitHub token from environment (optional, for higher rate limits)
    github_token = os.environ.get('GITHUB_TOKEN')

    discovery = SkillDiscovery(github_token=github_token, delay=args.delay)
    skills = discovery.discover_skills(limit=args.limit)
    discovery.save_results(skills, args.output)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 DISCOVERY SUMMARY")
    print("=" * 60)

    successful = [s for s in skills if s.fetch_status == 'success']
    print(f"\nSkills ready for evaluation: {len(successful)}")

    for skill in successful[:10]:
        content_len = len(skill.skill_md_content) if skill.skill_md_content else 0
        print(f"  ✅ {skill.name} ({content_len:,} chars) - {skill.repository}")

    if len(successful) > 10:
        print(f"  ... and {len(successful) - 10} more")

    # Show any that failed
    failed = [s for s in skills if s.fetch_status != 'success']
    if failed:
        print(f"\n⚠️  Skills not found: {len(failed)}")
        for skill in failed[:5]:
            print(f"  ❌ {skill.name} - {skill.repository}")


if __name__ == '__main__':
    main()
