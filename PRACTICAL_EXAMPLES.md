# Autopsy Pro v3 - Practical Examples & Recipes

## Introduction

This guide provides ready-to-use examples and workflows for common scenarios with Autopsy Pro v3.

## Quick Recipes

### 1. Daily Code Harvesting

**Goal**: Automatically collect quality code from your projects every day

```bash
#!/bin/bash
# daily_harvest.sh

DATE=$(date +%Y%m%d)
SCAN_DIR="$HOME/projects"
OUTPUT_DIR="$HOME/autopsy_harvests"

mkdir -p "$OUTPUT_DIR/scans"
mkdir -p "$OUTPUT_DIR/fragments"

# Scan for inactive projects (30+ days)
autopsy-pro scan "$SCAN_DIR" \
  --inactive-days 30 \
  --output "$OUTPUT_DIR/scans/scan_${DATE}.json" \
  --verbose

# Extract high-quality fragments
autopsy-pro extract \
  --scan-file "$OUTPUT_DIR/scans/scan_${DATE}.json" \
  --min-quality 7 \
  --skip-tests \
  --output "$OUTPUT_DIR/fragments/fragments_${DATE}.json"

echo "Harvest complete! Found:"
grep -o '"uid":' "$OUTPUT_DIR/fragments/fragments_${DATE}.json" | wc -l
echo "quality fragments"

# Add to crontab:
# 0 2 * * * /path/to/daily_harvest.sh
```

### 2. Build a Personal Utility Library

**Goal**: Extract your best utility functions for reuse

```bash
#!/bin/bash
# build_library.sh

# Scan all your projects
autopsy-pro scan ~/projects \
  --include-active \
  --output all_projects.json

# Extract high-quality code
autopsy-pro extract \
  --scan-file all_projects.json \
  --min-quality 8 \
  --skip-tests \
  --output all_fragments.json

# Export by language
for lang in python javascript go; do
  autopsy-pro export \
    --fragments-file all_fragments.json \
    --name "${lang}_utilities" \
    --description "High-quality ${lang} utility functions" \
    --language "$lang" \
    --min-quality 8
  
  echo "Exported ${lang} utilities"
done

echo "Library built! Check ~/.autopsy_pro/exports/"
```

### 3. Pre-Archive Code Extraction

**Goal**: Save valuable code before archiving old projects

```bash
#!/bin/bash
# pre_archive.sh

ARCHIVE_DIR="$1"

if [ -z "$ARCHIVE_DIR" ]; then
  echo "Usage: $0 <directory_to_archive>"
  exit 1
fi

# Scan everything, including active
autopsy-pro scan "$ARCHIVE_DIR" \
  --include-active \
  --output archive_scan.json

# Extract all decent code (quality >= 5)
autopsy-pro extract \
  --scan-file archive_scan.json \
  --min-quality 5 \
  --output archive_fragments.json

# Create a summary
echo "=== Archive Summary ===" > archive_summary.txt
echo "Directory: $ARCHIVE_DIR" >> archive_summary.txt
echo "Date: $(date)" >> archive_summary.txt
echo "" >> archive_summary.txt

# Count fragments
total=$(grep -o '"uid":' archive_fragments.json | wc -l)
echo "Total fragments saved: $total" >> archive_summary.txt

# Export the collection
autopsy-pro export \
  --fragments-file archive_fragments.json \
  --name "archive_$(basename $ARCHIVE_DIR)" \
  --description "Code extracted before archiving $ARCHIVE_DIR"

echo "Pre-archive extraction complete!"
cat archive_summary.txt
```

### 4. Team Code Sharing

**Goal**: Share best practices and patterns with your team

```bash
#!/bin/bash
# share_patterns.sh

PROJECT_DIR="$1"
PATTERN_NAME="$2"

# Scan the project
autopsy-pro scan "$PROJECT_DIR" \
  --include-active \
  --output team_scan.json

# Extract very high quality code
autopsy-pro extract \
  --scan-file team_scan.json \
  --min-quality 8 \
  --output team_fragments.json

# Export for sharing
autopsy-pro export \
  --fragments-file team_fragments.json \
  --name "${PATTERN_NAME}_patterns" \
  --description "Code patterns from $PROJECT_DIR"

# The export file can be shared with team
EXPORT_FILE="$HOME/.autopsy_pro/exports/${PATTERN_NAME}_patterns.json"
echo "Share this file with your team: $EXPORT_FILE"
```

### 5. Language Migration Helper

**Goal**: Extract Python code to help migrate to Go

```bash
#!/bin/bash
# migration_helper.sh

# Scan Python projects
autopsy-pro scan ~/python_projects \
  --output python_scan.json

# Extract Python code
autopsy-pro extract \
  --scan-file python_scan.json \
  --min-quality 6 \
  --output python_code.json

# Export just the logic (no tests)
autopsy-pro export \
  --fragments-file python_code.json \
  --name "python_to_migrate" \
  --description "Python code patterns to migrate to Go" \
  --language python \
  --skip-tests

echo "Python patterns extracted for migration reference"
```

### 6. Quality Audit

**Goal**: Audit code quality across all projects

```bash
#!/bin/bash
# quality_audit.sh

# Scan all projects
autopsy-pro scan ~/projects \
  --include-active \
  --output audit_scan.json \
  --verbose

# Extract all code (low threshold)
autopsy-pro extract \
  --scan-file audit_scan.json \
  --min-quality 1 \
  --output audit_fragments.json \
  --verbose

# Parse results for statistics
echo "=== Quality Audit Report ===" > audit_report.txt
echo "Date: $(date)" >> audit_report.txt
echo "" >> audit_report.txt

# Extract quality distribution (requires jq)
if command -v jq &> /dev/null; then
  echo "Quality Distribution:" >> audit_report.txt
  jq -r '.fragments[] | .quality' audit_fragments.json | \
    sort -n | uniq -c | \
    awk '{print "  Quality "$2": "$1" fragments"}' >> audit_report.txt
  
  echo "" >> audit_report.txt
  echo "Average Quality:" >> audit_report.txt
  jq '[.fragments[] | .quality] | add / length' audit_fragments.json >> audit_report.txt
else
  echo "Install jq for detailed statistics"
fi

cat audit_report.txt
```

## Configuration Recipes

### High Performance Setup

```bash
# Optimize for speed
autopsy-pro config --set parallel_scan=true
autopsy-pro config --set max_workers=8
autopsy-pro config --set enable_cache=true
autopsy-pro config --set cache_ttl_hours=48
```

### High Quality Setup

```bash
# Extract only the best
autopsy-pro config --set min_quality=7
autopsy-pro config --set min_lines=10
autopsy-pro config --set max_lines=200
autopsy-pro config --set skip_tests=true
autopsy-pro config --set deduplicate=true
```

### Comprehensive Coverage Setup

```bash
# Don't miss anything
autopsy-pro config --set min_quality=3
autopsy-pro config --set min_lines=5
autopsy-pro config --set max_lines=500
autopsy-pro config --set inactive_days=7
autopsy-pro config --set include_active=true
autopsy-pro config --set skip_tests=false
```

## Advanced Workflows

### Workflow 1: Weekly Learning Library Update

```bash
#!/bin/bash
# weekly_learning_update.sh

WEEK=$(date +%Y_W%V)

# Scan open source projects
autopsy-pro scan ~/oss_projects \
  --include-active \
  --output "scans/oss_${WEEK}.json"

# Extract well-documented code
autopsy-pro extract \
  --scan-file "scans/oss_${WEEK}.json" \
  --min-quality 8 \
  --output "fragments/learning_${WEEK}.json"

# Export by topic (using different quality thresholds)
for topic in "algorithms:9" "utilities:8" "patterns:8"; do
  name=${topic%:*}
  quality=${topic#*:}
  
  autopsy-pro export \
    --fragments-file "fragments/learning_${WEEK}.json" \
    --name "learning_${name}_${WEEK}" \
    --min-quality "$quality"
done

# Keep last 4 weeks only
find scans/ -name "oss_*.json" -mtime +28 -delete
find fragments/ -name "learning_*.json" -mtime +28 -delete

echo "Learning library updated for week $WEEK"
```

### Workflow 2: Multi-Project Analysis

```bash
#!/bin/bash
# multi_project_analysis.sh

# Directories to analyze
DIRS=(
  "$HOME/work_projects"
  "$HOME/personal_projects"
  "$HOME/open_source"
)

# Scan each separately
for dir in "${DIRS[@]}"; do
  name=$(basename "$dir")
  
  autopsy-pro scan "$dir" \
    --output "scans/${name}.json" \
    --verbose
  
  autopsy-pro extract \
    --scan-file "scans/${name}.json" \
    --min-quality 6 \
    --output "fragments/${name}.json"
done

# Combine results (requires jq)
if command -v jq &> /dev/null; then
  jq -s '{fragments: [.[] | .fragments[]] | unique_by(.uid)}' \
    fragments/*.json > combined_fragments.json
  
  echo "Combined analysis complete!"
  echo "Total unique fragments: $(jq '.fragments | length' combined_fragments.json)"
fi
```

### Workflow 3: Incremental Daily Scan

```bash
#!/bin/bash
# incremental_scan.sh

TODAY=$(date +%Y%m%d)
YESTERDAY=$(date -d "yesterday" +%Y%m%d 2>/dev/null || date -v-1d +%Y%m%d)

# Scan with 1 day threshold
autopsy-pro scan ~/projects \
  --inactive-days 1 \
  --output "scans/daily_${TODAY}.json"

# Extract new/changed code
autopsy-pro extract \
  --scan-file "scans/daily_${TODAY}.json" \
  --min-quality 6 \
  --output "fragments/daily_${TODAY}.json"

# Compare with yesterday (if exists)
if [ -f "fragments/daily_${YESTERDAY}.json" ]; then
  if command -v jq &> /dev/null; then
    # Find new fragments
    jq -s '
      (.[0].fragments | map(.uid)) as $old |
      (.[1].fragments | map(select(.uid | in($old | INDEX) | not)))
    ' "fragments/daily_${YESTERDAY}.json" "fragments/daily_${TODAY}.json" \
      > "fragments/new_${TODAY}.json"
    
    new_count=$(jq 'length' "fragments/new_${TODAY}.json")
    echo "Found $new_count new fragments today"
  fi
fi
```

## Integration Examples

### Git Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Extract from staged files
staged_files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|go)$')

if [ -n "$staged_files" ]; then
  # Quick quality check on staged code
  for file in $staged_files; do
    # Run extraction on just this file
    # (requires custom extraction script)
    echo "Quality checking: $file"
  done
fi
```

### CI/CD Integration (GitHub Actions)

```yaml
# .github/workflows/code-quality.yml
name: Code Quality Analysis

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install Autopsy Pro
        run: |
          pip install -e path/to/autopsy_pro_v3
      
      - name: Scan Repository
        run: |
          autopsy-pro scan . \
            --include-active \
            --output scan_results.json
      
      - name: Extract and Analyze
        run: |
          autopsy-pro extract \
            --scan-file scan_results.json \
            --min-quality 6 \
            --output fragments.json
      
      - name: Quality Report
        run: |
          # Generate quality report
          python scripts/quality_report.py fragments.json
```

### Makefile Integration

```makefile
# Makefile

.PHONY: scan extract analyze clean

SCAN_OUTPUT = .autopsy/scan.json
FRAGMENTS_OUTPUT = .autopsy/fragments.json

scan:
	@echo "Scanning project..."
	@mkdir -p .autopsy
	autopsy-pro scan . \
		--include-active \
		--output $(SCAN_OUTPUT)

extract: scan
	@echo "Extracting fragments..."
	autopsy-pro extract \
		--scan-file $(SCAN_OUTPUT) \
		--min-quality 7 \
		--output $(FRAGMENTS_OUTPUT)

analyze: extract
	@echo "Quality analysis:"
	@jq '[.fragments[] | .quality] | add / length' $(FRAGMENTS_OUTPUT)

export: extract
	@echo "Exporting collection..."
	autopsy-pro export \
		--fragments-file $(FRAGMENTS_OUTPUT) \
		--name "$(shell basename $(PWD))" \
		--description "Project code collection"

clean:
	@rm -rf .autopsy
	@autopsy-pro cache --clear
```

## Troubleshooting Recipes

### Fix Slow Scans

```bash
# Enable parallel processing
autopsy-pro config --set parallel_scan=true
autopsy-pro config --set max_workers=8

# Use cache
autopsy-pro config --set enable_cache=true

# Reduce file size limit
autopsy-pro config --set max_file_mb=0.5

# Re-scan
autopsy-pro scan ~/projects --output fast_scan.json
```

### Fix "No Fragments Found"

```bash
# Lower quality threshold
autopsy-pro config --set min_quality=3

# Lower line count minimums
autopsy-pro config --set min_lines=3

# Include test code
autopsy-pro config --set skip_tests=false

# Include active projects
autopsy-pro config --set include_active=true

# Re-extract
autopsy-pro extract --directory ~/projects --verbose
```

### Debug Extraction Issues

```bash
# Enable verbose logging
autopsy-pro extract \
  --directory ~/projects \
  --min-quality 1 \
  --verbose 2>&1 | tee extraction.log

# Check what was found
grep "Added project" extraction.log
grep "Extracted" extraction.log

# View actual config
autopsy-pro config --show
```

## Python API Usage

### Programmatic Scanning

```python
from autopsy_pro_v3 import scan_projects, extract_fragments, load_config
from pathlib import Path

# Load config
config = load_config()

# Customize
config.min_quality = 7
config.parallel_scan = True

# Scan
base_path = Path.home() / "projects"
scan_result = scan_projects(base_path, config)

print(f"Found {len(scan_result.projects)} projects")
print(f"Total code files: {scan_result.total_code_files}")

# Extract
extraction_result = extract_fragments(scan_result.projects, config)

print(f"Extracted {len(extraction_result.fragments)} fragments")
print(f"Average quality: {extraction_result.avg_quality:.1f}/10")

# Filter high quality
high_quality = [f for f in extraction_result.fragments if f.quality >= 8]
print(f"High quality fragments: {len(high_quality)}")
```

### Custom Analysis

```python
from autopsy_pro_v3.models import Fragment, ExtractionResult
import json

# Load fragments
with open('fragments.json', 'r') as f:
    data = json.load(f)

result = ExtractionResult.from_dict(data)

# Analyze by language
by_language = {}
for frag in result.fragments:
    lang = frag.language
    by_language.setdefault(lang, []).append(frag)

for lang, frags in sorted(by_language.items()):
    avg_quality = sum(f.quality for f in frags) / len(frags)
    print(f"{lang}: {len(frags)} fragments, avg quality {avg_quality:.1f}")

# Find complex fragments
complex_frags = [f for f in result.fragments if f.complexity > 10]
for frag in complex_frags:
    print(f"Complex: {frag.name} (complexity: {frag.complexity})")
```

---

**Remember**: These are starting points. Customize them for your specific needs!
