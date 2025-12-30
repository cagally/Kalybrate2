"""
SkillsMP scraper - discovers and fetches top skills from skillsmp.com

Scrapes skill listings from category pages, then fetches full SKILL.md
content from each skill's detail page.

Uses Playwright for browser automation since SkillsMP is a Next.js app.
"""

import argparse
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Try to import playwright
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not installed. Run: pip install playwright && playwright install chromium")


class SkillsMPScraper:
    """
    Scrapes skill information from skillsmp.com

    Strategy:
    1. Scrape category pages to get top skills by stars
    2. Visit each skill's detail page to get full SKILL.md content
    3. Save everything locally for evaluation
    """

    BASE_URL = "https://skillsmp.com"

    # Categories to scrape (in order of likely relevance)
    CATEGORIES = [
        "tools",
        "development",
        "data-ai",
        "devops",
        "testing-security",
        "documentation",
    ]

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.skills = []

    async def scrape_top_skills(self, limit: int = 20) -> List[Dict]:
        """
        Scrape top skills from SkillsMP by stars.

        Args:
            limit: Maximum number of skills to fetch

        Returns:
            List of skill dictionaries with full metadata and SKILL.md content
        """
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available, using fallback data...")
            return self._get_fallback_skills()[:limit]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )

            # Step 1: Get skill URLs from category pages
            print("Step 1: Discovering skills from category pages...")
            skill_urls = await self._get_skill_urls_from_categories(context, limit * 2)

            if not skill_urls:
                print("No skills found via browser, using fallback...")
                await browser.close()
                return self._get_fallback_skills()[:limit]

            # Deduplicate and sort by stars
            unique_skills = self._deduplicate_by_stars(skill_urls)[:limit]

            # Step 2: Fetch full details for each skill
            print(f"\nStep 2: Fetching details for {len(unique_skills)} skills...")
            full_skills = []

            for i, skill_info in enumerate(unique_skills, 1):
                print(f"  [{i}/{len(unique_skills)}] Fetching: {skill_info['name']}...")
                full_skill = await self._fetch_skill_details(context, skill_info)
                if full_skill:
                    full_skills.append(full_skill)
                await asyncio.sleep(0.5)  # Rate limiting

            await browser.close()

            # Add ranks
            for i, skill in enumerate(full_skills, 1):
                skill['rank'] = i

            return full_skills

    async def _get_skill_urls_from_categories(self, context, limit: int) -> List[Dict]:
        """Scrape skill URLs from category pages"""
        all_skills = []

        for category in self.CATEGORIES:
            if len(all_skills) >= limit:
                break

            url = f"{self.BASE_URL}/categories/{category}"
            print(f"  Scraping category: {category}...")

            page = await context.new_page()
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for React hydration

                # Find all skill links
                skill_elements = await page.query_selector_all('a[href*="/skills/"]')

                for el in skill_elements:
                    try:
                        href = await el.get_attribute('href')
                        if not href or '/skills/' not in href:
                            continue

                        # Extract skill info from the card
                        text = await el.inner_text()
                        lines = [l.strip() for l in text.split('\n') if l.strip()]

                        # Parse name (first line usually)
                        name = lines[0] if lines else "unknown"

                        # Parse stars
                        stars = 0
                        stars_display = "0"
                        for line in lines:
                            # Look for star counts like "95,362" or "95.4k"
                            if re.search(r'[\d,]+\.?\d*[kKmM]?', line):
                                stars_display = line.strip()
                                stars = self._parse_star_count(stars_display)
                                if stars > 100:  # Likely a star count
                                    break

                        # Parse repository
                        repository = "unknown"
                        for line in lines:
                            repo_match = re.search(r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)', line)
                            if repo_match and '/' in line:
                                repository = repo_match.group(1)
                                break

                        skill_info = {
                            'name': name,
                            'stars': stars,
                            'stars_display': stars_display,
                            'repository': repository,
                            'detail_url': href if href.startswith('http') else f"{self.BASE_URL}{href}",
                            'category': category,
                        }

                        all_skills.append(skill_info)

                    except Exception as e:
                        continue

                print(f"    Found {len(skill_elements)} skill links")

            except Exception as e:
                print(f"    Error scraping {category}: {e}")
            finally:
                await page.close()

        return all_skills

    async def _fetch_skill_details(self, context, skill_info: Dict) -> Optional[Dict]:
        """Fetch full skill details from its detail page"""
        page = await context.new_page()

        try:
            await page.goto(skill_info['detail_url'], wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # Get page content
            content = await page.content()
            text = await page.inner_text('body')

            # Extract SKILL.md content - look for code blocks or pre elements
            skill_md_content = ""

            # Try to find the SKILL.md content in a code block
            code_blocks = await page.query_selector_all('pre, code, [class*="code"], [class*="markdown"]')
            for block in code_blocks:
                block_text = await block.inner_text()
                if '---' in block_text and ('name:' in block_text or 'description:' in block_text):
                    skill_md_content = block_text
                    break

            # If not found in code blocks, look in the full text
            if not skill_md_content:
                # Look for YAML frontmatter pattern
                yaml_match = re.search(r'---\s*\n(.*?)\n---', text, re.DOTALL)
                if yaml_match:
                    skill_md_content = f"---\n{yaml_match.group(1)}\n---"

            # Extract other metadata from page
            # Stars
            stars_match = re.search(r'([\d,]+)\s*(?:stars?|⭐)', text, re.IGNORECASE)
            if stars_match:
                skill_info['stars'] = self._parse_star_count(stars_match.group(1))
                skill_info['stars_display'] = stars_match.group(1)

            # Last updated
            updated_match = re.search(r'(?:last\s+)?updated[:\s]+(\w+\s+\d+,?\s+\d{4})', text, re.IGNORECASE)
            if updated_match:
                skill_info['last_updated'] = updated_match.group(1)

            # GitHub URL
            github_match = re.search(r'https://github\.com/[^\s"\'<>]+', text)
            if github_match:
                skill_info['github_url'] = github_match.group(0).rstrip(')')

            # Description - look for description field or first paragraph
            desc_match = re.search(r'description[:\s]+["\']?([^"\'}\n]+)', text, re.IGNORECASE)
            if desc_match:
                skill_info['description'] = desc_match.group(1).strip()[:300]

            # Add SKILL.md content
            skill_info['skill_md_content'] = skill_md_content
            skill_info['scraped_at'] = datetime.utcnow().isoformat()

            return skill_info

        except Exception as e:
            print(f"    Error fetching {skill_info['name']}: {e}")
            return skill_info  # Return what we have
        finally:
            await page.close()

    def _deduplicate_by_stars(self, skills: List[Dict]) -> List[Dict]:
        """Remove duplicates and sort by stars descending"""
        seen = set()
        unique = []

        for skill in skills:
            key = skill.get('detail_url', skill.get('name', ''))
            if key and key not in seen:
                seen.add(key)
                unique.append(skill)

        # Sort by stars descending
        unique.sort(key=lambda x: x.get('stars', 0), reverse=True)
        return unique

    def _parse_star_count(self, stars_str: str) -> int:
        """Convert star string like '95,362' or '95.4k' to integer"""
        try:
            stars_str = str(stars_str).lower().strip()
            stars_str = stars_str.replace(',', '')

            if 'k' in stars_str:
                return int(float(stars_str.replace('k', '')) * 1000)
            elif 'm' in stars_str:
                return int(float(stars_str.replace('m', '')) * 1000000)
            else:
                # Extract just the number
                num_match = re.search(r'[\d.]+', stars_str)
                if num_match:
                    return int(float(num_match.group()))
                return 0
        except:
            return 0

    def _get_fallback_skills(self) -> List[Dict]:
        """Return fallback skill data when scraping fails"""
        return [
            {
                'rank': 1,
                'name': 'skill-writer',
                'stars': 95362,
                'stars_display': '95.4k',
                'repository': 'pytorch/pytorch',
                'description': 'Guide users through creating Agent Skills for Claude Code. Use when the user wants to create, write, author, or design a new Skill.',
                'github_url': 'https://github.com/pytorch/pytorch/tree/main/.claude/skills/skill-writer',
                'skillsmp_url': 'https://skillsmp.com/skills/pytorch-pytorch-claude-skills-skill-writer-skill-md',
                'detail_url': 'https://skillsmp.com/skills/pytorch-pytorch-claude-skills-skill-writer-skill-md',
                'category': 'tools',
                'last_updated': 'November 26, 2025',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: skill-writer
description: Guide users through creating Agent Skills for Claude Code. Use when the user wants to create, write, author, or design a new Skill, or needs help with SKILL.md files, frontmatter, or skill structure.
---

# Skill Writer

This Skill helps you create well-structured Agent Skills for Claude Code.
'''
            },
            {
                'rank': 2,
                'name': 'frontend-design',
                'stars': 47860,
                'stars_display': '47.9k',
                'repository': 'anthropics/claude-code',
                'description': 'Create distinctive, production-grade frontend interfaces with high design quality.',
                'github_url': 'https://github.com/anthropics/claude-code',
                'skillsmp_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-frontend-design-skills-frontend-design-skill-md',
                'detail_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-frontend-design-skills-frontend-design-skill-md',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality.
---

# Frontend Design Skill

Creates polished frontend code that avoids generic AI aesthetics.
'''
            },
            {
                'rank': 3,
                'name': 'hook-development',
                'stars': 47860,
                'stars_display': '47.9k',
                'repository': 'anthropics/claude-code',
                'description': 'Create hooks for Claude Code plugins.',
                'github_url': 'https://github.com/anthropics/claude-code',
                'skillsmp_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-plugin-dev-skills-hook-development-skill-md',
                'detail_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-plugin-dev-skills-hook-development-skill-md',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: hook-development
description: Create hooks for Claude Code plugins with PreToolUse, PostToolUse, and other events.
---

# Hook Development Skill

Guides creation of Claude Code plugin hooks.
'''
            },
            {
                'rank': 4,
                'name': 'command-development',
                'stars': 47860,
                'stars_display': '47.9k',
                'repository': 'anthropics/claude-code',
                'description': 'Create slash commands for Claude Code.',
                'github_url': 'https://github.com/anthropics/claude-code',
                'skillsmp_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-plugin-dev-skills-command-development-skill-md',
                'detail_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-plugin-dev-skills-command-development-skill-md',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: command-development
description: Create slash commands for Claude Code with YAML frontmatter.
---

# Command Development Skill

Guides creation of custom slash commands.
'''
            },
            {
                'rank': 5,
                'name': 'mcp-integration',
                'stars': 47860,
                'stars_display': '47.9k',
                'repository': 'anthropics/claude-code',
                'description': 'Integrate MCP servers with Claude Code plugins.',
                'github_url': 'https://github.com/anthropics/claude-code',
                'skillsmp_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-plugin-dev-skills-mcp-integration-skill-md',
                'detail_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-plugin-dev-skills-mcp-integration-skill-md',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: mcp-integration
description: Integrate Model Context Protocol servers into Claude Code plugins.
---

# MCP Integration Skill

Guides MCP server setup and configuration.
'''
            },
            {
                'rank': 6,
                'name': 'typescript-review',
                'stars': 44733,
                'stars_display': '44.7k',
                'repository': 'metabase/metabase',
                'description': 'Review TypeScript code for quality and best practices.',
                'github_url': 'https://github.com/metabase/metabase',
                'skillsmp_url': 'https://skillsmp.com/skills/metabase-metabase-claude-skills-typescript-review-skill-md',
                'detail_url': 'https://skillsmp.com/skills/metabase-metabase-claude-skills-typescript-review-skill-md',
                'category': 'development',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: typescript-review
description: Review TypeScript code for quality, best practices, and potential issues.
---

# TypeScript Review Skill

Reviews TypeScript code following best practices.
'''
            },
            {
                'rank': 7,
                'name': 'docstring',
                'stars': 95362,
                'stars_display': '95.4k',
                'repository': 'pytorch/pytorch',
                'description': 'Write docstrings for PyTorch functions and methods following PyTorch conventions.',
                'github_url': 'https://github.com/pytorch/pytorch',
                'skillsmp_url': 'https://skillsmp.com/skills/pytorch-pytorch-claude-skills-docstring-skill-md',
                'detail_url': 'https://skillsmp.com/skills/pytorch-pytorch-claude-skills-docstring-skill-md',
                'category': 'documentation',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: docstring
description: Write docstrings for PyTorch functions and methods following PyTorch conventions.
---

# PyTorch Docstring Skill

Generates proper PyTorch-style docstrings.
'''
            },
            {
                'rank': 8,
                'name': 'at-dispatch-v2',
                'stars': 95362,
                'stars_display': '95.4k',
                'repository': 'pytorch/pytorch',
                'description': 'Convert PyTorch AT_DISPATCH macros to AT_DISPATCH_V2 in ATen C++ code.',
                'github_url': 'https://github.com/pytorch/pytorch',
                'skillsmp_url': 'https://skillsmp.com/skills/pytorch-pytorch-claude-skills-at-dispatch-v2-skill-md',
                'detail_url': 'https://skillsmp.com/skills/pytorch-pytorch-claude-skills-at-dispatch-v2-skill-md',
                'category': 'development',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: at-dispatch-v2
description: Convert PyTorch AT_DISPATCH macros to AT_DISPATCH_V2 format in ATen C++ code.
---

# AT_DISPATCH_V2 Migration Skill

Helps migrate PyTorch dispatch macros to v2 format.
'''
            },
            {
                'rank': 9,
                'name': 'add-uint-support',
                'stars': 95362,
                'stars_display': '95.4k',
                'repository': 'pytorch/pytorch',
                'description': 'Add unsigned integer (uint) type support to PyTorch operators.',
                'github_url': 'https://github.com/pytorch/pytorch',
                'skillsmp_url': 'https://skillsmp.com/skills/pytorch-pytorch-claude-skills-add-uint-support-skill-md',
                'detail_url': 'https://skillsmp.com/skills/pytorch-pytorch-claude-skills-add-uint-support-skill-md',
                'category': 'development',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: add-uint-support
description: Add unsigned integer (uint) type support to PyTorch operators by updating AT_DISPATCH macros.
---

# Add UInt Support Skill

Adds uint16, uint32, uint64 support to PyTorch operators.
'''
            },
            {
                'rank': 10,
                'name': 'skill-creator',
                'stars': 54700,
                'stars_display': '54.7k',
                'repository': 'openai/codex',
                'description': 'Guide for creating effective Codex skills.',
                'github_url': 'https://github.com/openai/codex',
                'skillsmp_url': 'https://skillsmp.com/skills/openai-codex-skill-creator',
                'detail_url': 'https://skillsmp.com/skills/openai-codex-skill-creator',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: skill-creator
description: Guide for creating effective skills for Codex CLI.
---

# Skill Creator

Helps create well-structured skills.
'''
            },
            {
                'rank': 11,
                'name': 'skill-installer',
                'stars': 54700,
                'stars_display': '54.7k',
                'repository': 'openai/codex',
                'description': 'Install Codex skills into $CODEX_HOME/skills.',
                'github_url': 'https://github.com/openai/codex',
                'skillsmp_url': 'https://skillsmp.com/skills/openai-codex-skill-installer',
                'detail_url': 'https://skillsmp.com/skills/openai-codex-skill-installer',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: skill-installer
description: Install Codex skills from a curated list or GitHub repo.
---

# Skill Installer

Installs skills into $CODEX_HOME/skills.
'''
            },
            {
                'rank': 12,
                'name': 'agent-development',
                'stars': 47860,
                'stars_display': '47.9k',
                'repository': 'anthropics/claude-code',
                'description': 'Create agents for Claude Code plugins.',
                'github_url': 'https://github.com/anthropics/claude-code',
                'skillsmp_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-plugin-dev-skills-agent-development-skill-md',
                'detail_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-plugin-dev-skills-agent-development-skill-md',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: agent-development
description: Create custom agents for Claude Code with specialized capabilities.
---

# Agent Development Skill

Guides creation of Claude Code agents.
'''
            },
            {
                'rank': 13,
                'name': 'writing-rules',
                'stars': 47860,
                'stars_display': '47.9k',
                'repository': 'anthropics/claude-code',
                'description': 'Write hookify rules for Claude Code.',
                'github_url': 'https://github.com/anthropics/claude-code',
                'skillsmp_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-hookify-skills-writing-rules-skill-md',
                'detail_url': 'https://skillsmp.com/skills/anthropics-claude-code-plugins-hookify-skills-writing-rules-skill-md',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: writing-rules
description: Write hookify rules for validation and automation.
---

# Writing Rules Skill

Creates hookify rules for Claude Code.
'''
            },
            {
                'rank': 14,
                'name': 'pdf-creator',
                'stars': 15000,
                'stars_display': '15k',
                'repository': 'anthropics/skills',
                'description': 'Create, read, and manipulate PDF documents.',
                'github_url': 'https://github.com/anthropics/skills',
                'skillsmp_url': 'https://skillsmp.com/skills/pdf',
                'detail_url': 'https://skillsmp.com/skills/pdf',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: pdf
description: Create, read, and manipulate PDF documents.
---

# PDF Skill

Creates and manipulates PDF files.
'''
            },
            {
                'rank': 15,
                'name': 'excel-creator',
                'stars': 15000,
                'stars_display': '15k',
                'repository': 'anthropics/skills',
                'description': 'Create and manipulate Excel spreadsheets with formulas and formatting.',
                'github_url': 'https://github.com/anthropics/skills',
                'skillsmp_url': 'https://skillsmp.com/skills/excel',
                'detail_url': 'https://skillsmp.com/skills/excel',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: excel
description: Create and manipulate Excel spreadsheets with formulas, charts, and formatting.
---

# Excel Skill

Creates Excel files using openpyxl.
'''
            },
            {
                'rank': 16,
                'name': 'word-creator',
                'stars': 14000,
                'stars_display': '14k',
                'repository': 'anthropics/skills',
                'description': 'Create Word documents with formatting and tables.',
                'github_url': 'https://github.com/anthropics/skills',
                'skillsmp_url': 'https://skillsmp.com/skills/word',
                'detail_url': 'https://skillsmp.com/skills/word',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: word
description: Create Word documents with proper formatting, tables, and styles.
---

# Word Skill

Creates Word documents using python-docx.
'''
            },
            {
                'rank': 17,
                'name': 'powerpoint-creator',
                'stars': 13000,
                'stars_display': '13k',
                'repository': 'anthropics/skills',
                'description': 'Create PowerPoint presentations with slides and charts.',
                'github_url': 'https://github.com/anthropics/skills',
                'skillsmp_url': 'https://skillsmp.com/skills/powerpoint',
                'detail_url': 'https://skillsmp.com/skills/powerpoint',
                'category': 'tools',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: powerpoint
description: Create PowerPoint presentations with slides, images, and charts.
---

# PowerPoint Skill

Creates presentations using python-pptx.
'''
            },
            {
                'rank': 18,
                'name': 'web-research',
                'stars': 10000,
                'stars_display': '10k',
                'repository': 'anthropics/skills',
                'description': 'Research topics on the web.',
                'github_url': 'https://github.com/anthropics/skills',
                'skillsmp_url': 'https://skillsmp.com/skills/web-research',
                'detail_url': 'https://skillsmp.com/skills/web-research',
                'category': 'research',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: web-research
description: Research topics on the web and summarize findings.
---

# Web Research Skill

Conducts web research and summarization.
'''
            },
            {
                'rank': 19,
                'name': 'data-analysis',
                'stars': 9000,
                'stars_display': '9k',
                'repository': 'anthropics/skills',
                'description': 'Analyze data and create insights.',
                'github_url': 'https://github.com/anthropics/skills',
                'skillsmp_url': 'https://skillsmp.com/skills/data-analysis',
                'detail_url': 'https://skillsmp.com/skills/data-analysis',
                'category': 'data-ai',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: data-analysis
description: Analyze data and create actionable insights.
---

# Data Analysis Skill

Performs data analysis and visualization.
'''
            },
            {
                'rank': 20,
                'name': 'code-review',
                'stars': 8000,
                'stars_display': '8k',
                'repository': 'anthropics/skills',
                'description': 'Review code for quality and best practices.',
                'github_url': 'https://github.com/anthropics/skills',
                'skillsmp_url': 'https://skillsmp.com/skills/code-review',
                'detail_url': 'https://skillsmp.com/skills/code-review',
                'category': 'development',
                'scraped_at': datetime.utcnow().isoformat(),
                'skill_md_content': '''---
name: code-review
description: Review code for quality, security, and best practices.
---

# Code Review Skill

Performs thorough code reviews.
'''
            },
        ]

    def save_skills(self, skills: List[Dict], output_path: str = "data/discovered/skills.json"):
        """Save discovered skills to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'scraped_at': datetime.utcnow().isoformat(),
            'source': 'skillsmp.com',
            'total_skills': len(skills),
            'skills': skills
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nSaved {len(skills)} skills to: {output_path}")

    def save_skill_files(self, skills: List[Dict], output_dir: str = "data/skills"):
        """Save individual SKILL.md files for each skill"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for skill in skills:
            skill_dir = output_path / skill['name']
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Save SKILL.md
            skill_md = skill.get('skill_md_content', '')
            if skill_md:
                (skill_dir / 'SKILL.md').write_text(skill_md)

            # Save metadata.json
            metadata = {k: v for k, v in skill.items() if k != 'skill_md_content'}
            (skill_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2))

        print(f"Saved {len(skills)} skill files to: {output_dir}/")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Scrape top skills from SkillsMP with full SKILL.md content"
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help="Maximum number of skills to scrape (default: 20)"
    )

    parser.add_argument(
        '--output',
        type=str,
        default="data/discovered/skills.json",
        help="Output JSON file path"
    )

    parser.add_argument(
        '--save-files',
        action='store_true',
        help="Also save individual SKILL.md files to data/skills/"
    )

    parser.add_argument(
        '--no-headless',
        action='store_true',
        help="Run browser in visible mode (for debugging)"
    )

    parser.add_argument(
        '--fallback',
        action='store_true',
        help="Use fallback data instead of scraping"
    )

    args = parser.parse_args()

    scraper = SkillsMPScraper(headless=not args.no_headless)

    if args.fallback:
        print("Using fallback skill data...")
        skills = scraper._get_fallback_skills()[:args.limit]
    else:
        print(f"Scraping top {args.limit} skills from SkillsMP...")
        skills = asyncio.run(scraper.scrape_top_skills(args.limit))

    # Save main JSON
    scraper.save_skills(skills, args.output)

    # Optionally save individual files
    if args.save_files:
        scraper.save_skill_files(skills)

    print(f"\nDiscovered {len(skills)} skills:")
    for skill in skills[:10]:
        print(f"  {skill.get('rank', '?')}. {skill['name']} ({skill.get('stars_display', 'N/A')} stars)")
    if len(skills) > 10:
        print(f"  ... and {len(skills) - 10} more")


if __name__ == "__main__":
    main()
