#!/bin/bash
# Kalybrate Full Evaluation Pipeline
# Run this to scrape, fetch, evaluate, and update the website

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================"
echo "KALYBRATE FULL EVALUATION PIPELINE"
echo "========================================"
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY not set"
    echo "Run: export ANTHROPIC_API_KEY=your-key-here"
    exit 1
fi

# Step 1: Scrape skills from SkillsMP
echo "[1/5] Scraping skills from SkillsMP..."
python3 -m discovery.skillsmp_scraper --limit 20 --fallback

# Step 2: Fetch SKILL.md files from GitHub
echo ""
echo "[2/5] Fetching SKILL.md files from GitHub..."
python3 -m discovery.github_fetcher --limit 20 || true

# Step 3: Run evaluations
echo ""
echo "[3/5] Running evaluations..."
python3 -m evaluator.main --all

# Step 4: Export to website
echo ""
echo "[4/5] Exporting results to website..."
cp data/scores/*.json website/src/data/ 2>/dev/null || true

# Step 5: Build website
echo ""
echo "[5/5] Building website..."
cd website
npm run build

echo ""
echo "========================================"
echo "PIPELINE COMPLETE!"
echo "========================================"
echo ""
echo "Results saved to: data/scores/"
echo "Website built to: website/dist/"
echo ""
echo "To view results: cd website && npm run dev"
