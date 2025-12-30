"""
SKILL.md parser - extracts frontmatter and metadata from SKILL.md files
"""

import re
from pathlib import Path
from typing import Dict, Optional
import yaml


class SkillParser:
    """Parse SKILL.md files and extract metadata"""

    def __init__(self):
        """Initialize parser"""
        pass

    def extract_frontmatter(self, content: str) -> Optional[Dict]:
        """
        Extract YAML frontmatter from markdown content.

        SKILL.md files typically have frontmatter like:
        ---
        name: skill-name
        description: Description
        tags: [tag1, tag2]
        ---

        Args:
            content: Full SKILL.md content

        Returns:
            Dict of frontmatter fields or None if not found
        """
        # Match YAML frontmatter between --- delimiters
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

        if match:
            yaml_content = match.group(1)
            try:
                frontmatter = yaml.safe_load(yaml_content)
                return frontmatter
            except yaml.YAMLError as e:
                print(f"Error parsing YAML frontmatter: {e}")
                return None

        return None

    def extract_examples(self, content: str) -> list:
        """
        Extract example usage from SKILL.md content.

        Args:
            content: SKILL.md content

        Returns:
            List of example strings
        """
        examples = []

        # Look for sections titled "Examples", "Usage", etc.
        sections = re.split(r'\n##\s+', content)

        for section in sections:
            if any(keyword in section.lower() for keyword in ['example', 'usage']):
                # Extract code blocks
                code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', section, re.DOTALL)
                examples.extend(code_blocks)

        return examples

    def parse_skill_file(self, file_path: str) -> Dict:
        """
        Parse a SKILL.md file and extract all metadata.

        Args:
            file_path: Path to SKILL.md file

        Returns:
            Dict with parsed skill information
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"SKILL.md not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        frontmatter = self.extract_frontmatter(content)

        # Extract examples
        examples = self.extract_examples(content)

        # Build result
        result = {
            'file_path': str(file_path),
            'name': None,
            'description': None,
            'tags': [],
            'examples': examples,
            'frontmatter': frontmatter or {}
        }

        # Populate from frontmatter
        if frontmatter:
            result['name'] = frontmatter.get('name')
            result['description'] = frontmatter.get('description')
            result['tags'] = frontmatter.get('tags', [])

        # If no name in frontmatter, use directory name
        if not result['name']:
            result['name'] = file_path.parent.name

        return result

    def parse_skills_directory(self, directory: str) -> list:
        """
        Parse all SKILL.md files in a directory.

        Args:
            directory: Directory containing skill subdirectories

        Returns:
            List of parsed skill dictionaries
        """
        directory = Path(directory)

        if not directory.exists():
            print(f"Directory not found: {directory}")
            return []

        skills = []

        # Find all SKILL.md files
        for skill_file in directory.glob('*/SKILL.md'):
            try:
                skill = self.parse_skill_file(skill_file)
                skills.append(skill)
                print(f"Parsed: {skill['name']}")
            except Exception as e:
                print(f"Error parsing {skill_file}: {e}")
                continue

        return skills


def parse_skill(file_path: str) -> Dict:
    """
    Quick helper function to parse a single SKILL.md file.

    Args:
        file_path: Path to SKILL.md

    Returns:
        Parsed skill dictionary
    """
    parser = SkillParser()
    return parser.parse_skill_file(file_path)


def main():
    """CLI entry point"""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Parse SKILL.md files"
    )

    parser.add_argument(
        '--directory',
        type=str,
        default="data/skills",
        help="Directory containing skills (default: data/skills)"
    )

    parser.add_argument(
        '--output',
        type=str,
        help="Output JSON file (optional)"
    )

    args = parser.parse_args()

    # Parse skills
    skill_parser = SkillParser()
    skills = skill_parser.parse_skills_directory(args.directory)

    print(f"\n\nParsed {len(skills)} skills:")
    for skill in skills:
        print(f"  - {skill['name']}: {skill.get('description', 'No description')[:60]}")

    # Save if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(skills, f, indent=2)

        print(f"\nSaved to: {args.output}")


if __name__ == "__main__":
    main()
