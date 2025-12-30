"""
GitHub fetcher - fetches SKILL.md files from GitHub repositories
"""

import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import requests


class GitHubFetcher:
    """Fetches SKILL.md files from GitHub repos"""

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub fetcher.

        Args:
            github_token: Optional GitHub API token for higher rate limits
        """
        self.session = requests.Session()

        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Kalybrate-Skill-Fetcher'
        }

        if github_token:
            headers['Authorization'] = f'token {github_token}'

        self.session.headers.update(headers)

    def parse_github_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Parse GitHub URL to extract owner and repo.

        Args:
            url: GitHub URL

        Returns:
            Dict with 'owner' and 'repo' or None if invalid
        """
        # Handle various GitHub URL formats
        url = url.rstrip('/')

        if 'github.com' not in url:
            return None

        try:
            # Remove protocol and domain
            path = url.split('github.com/')[-1]

            # Remove trailing .git if present
            if path.endswith('.git'):
                path = path[:-4]

            parts = path.split('/')
            if len(parts) >= 2:
                return {
                    'owner': parts[0],
                    'repo': parts[1]
                }
        except Exception:
            pass

        return None

    def fetch_skill_md(self, owner: str, repo: str) -> Optional[str]:
        """
        Fetch SKILL.md file from GitHub repo.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Contents of SKILL.md or None if not found
        """
        # Try different possible locations and filenames
        possible_paths = [
            'SKILL.md',
            'skill.md',
            'Skill.md',
            'docs/SKILL.md',
            '.skill/SKILL.md'
        ]

        for path in possible_paths:
            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'

            try:
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    # GitHub API returns base64 encoded content
                    import base64
                    content = base64.b64decode(data['content']).decode('utf-8')

                    print(f"  Found SKILL.md at: {path}")
                    return content

            except Exception as e:
                continue

        print(f"  SKILL.md not found in repo")
        return None

    def fetch_skill_from_url(self, github_url: str) -> Optional[Dict]:
        """
        Fetch skill metadata from GitHub URL.

        Args:
            github_url: GitHub repository URL

        Returns:
            Dict with skill info or None if failed
        """
        parsed = self.parse_github_url(github_url)

        if not parsed:
            print(f"Invalid GitHub URL: {github_url}")
            return None

        owner = parsed['owner']
        repo = parsed['repo']

        print(f"Fetching from {owner}/{repo}...")

        skill_md = self.fetch_skill_md(owner, repo)

        if skill_md:
            return {
                'owner': owner,
                'repo': repo,
                'github_url': github_url,
                'skill_md_content': skill_md
            }

        return None

    def fetch_multiple_skills(
        self,
        github_urls: List[str],
        max_skills: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch SKILL.md files from multiple GitHub repos.

        Args:
            github_urls: List of GitHub URLs
            max_skills: Optional limit on number to fetch

        Returns:
            List of successfully fetched skills
        """
        skills = []
        limit = max_skills or len(github_urls)

        for i, url in enumerate(github_urls[:limit]):
            print(f"\nFetching skill {i+1}/{min(limit, len(github_urls))}")

            skill = self.fetch_skill_from_url(url)

            if skill:
                skills.append(skill)

            # Rate limiting
            time.sleep(0.5)

        return skills

    def save_skill(self, skill: Dict, output_dir: str = "data/skills"):
        """
        Save skill to directory.

        Args:
            skill: Skill dictionary with content
            output_dir: Base directory for skills
        """
        skill_name = skill['repo']
        skill_dir = Path(output_dir) / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Save SKILL.md
        with open(skill_dir / "SKILL.md", 'w') as f:
            f.write(skill['skill_md_content'])

        # Save metadata
        metadata = {
            'owner': skill['owner'],
            'repo': skill['repo'],
            'github_url': skill['github_url']
        }

        with open(skill_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"  Saved to: {skill_dir}")

    def save_skills(self, skills: List[Dict], output_dir: str = "data/skills"):
        """
        Save multiple skills.

        Args:
            skills: List of skill dictionaries
            output_dir: Base directory for skills
        """
        for skill in skills:
            self.save_skill(skill, output_dir)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Fetch SKILL.md files from GitHub"
    )

    parser.add_argument(
        '--input',
        type=str,
        default="data/discovered/skills.json",
        help="Input JSON file with discovered skills (default: data/discovered/skills.json)"
    )

    parser.add_argument(
        '--limit',
        type=int,
        help="Maximum number of skills to fetch"
    )

    parser.add_argument(
        '--output',
        type=str,
        default="data/skills",
        help="Output directory for skills (default: data/skills)"
    )

    parser.add_argument(
        '--token',
        type=str,
        help="GitHub API token (optional, for higher rate limits)"
    )

    args = parser.parse_args()

    # Load discovered skills
    input_file = Path(args.input)

    if not input_file.exists():
        print(f"Error: Input file not found: {args.input}")
        print("Run skillsmp_scraper.py first to discover skills")
        return

    with open(input_file, 'r') as f:
        discovered_skills = json.load(f)

    print(f"Loaded {len(discovered_skills)} discovered skills")

    # Extract GitHub URLs
    github_urls = [
        skill['github_url']
        for skill in discovered_skills
        if skill.get('github_url')
    ]

    print(f"Found {len(github_urls)} GitHub URLs")

    if not github_urls:
        print("No GitHub URLs found. Nothing to fetch.")
        return

    # Fetch skills
    fetcher = GitHubFetcher(github_token=args.token)
    skills = fetcher.fetch_multiple_skills(github_urls, max_skills=args.limit)

    print(f"\n\nSuccessfully fetched {len(skills)} skills")

    # Save results
    fetcher.save_skills(skills, args.output)

    print(f"\nAll skills saved to: {args.output}")


if __name__ == "__main__":
    main()
