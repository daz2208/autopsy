# Quick Start Guide - Autopsy Pro v3

This guide will get you up and running with Autopsy Pro v3 in minutes.

## Installation

```bash
# Navigate to the project directory
cd autopsy_pro_v3

# Install the package
pip install -e .

# Or install with all features
pip install -e ".[all]"
```

## Your First Scan

Let's scan your home projects directory:

```bash
# Scan for inactive projects (>60 days old)
autopsy-pro scan ~/projects --output my_scan.json --verbose
```

You'll see output like:

```
Scanning /Users/you/projects...
Found 12 potential project roots
Added project: my-old-app (Django) - 45 code files
Added project: react-dashboard (React) - 67 code files
...
Scan complete: Found 8 projects in 3.4s

Scan Results:
  Projects found: 8
  Total files: 1,234
  Code files: 456
  Total size: 12.3 MB
  Scan time: 3.42s
```

## Extract Quality Code

Now extract high-quality fragments:

```bash
# Extract fragments with quality >= 6
autopsy-pro extract \
  --scan-file my_scan.json \
  --min-quality 6 \
  --output my_fragments.json \
  --verbose
```

Output:

```
Extracting fragments...
Extracted 892 raw fragments
Deduplicated: 892 -> 734 fragments
Extraction complete: 734 fragments in 5.2s

Extraction Results:
  Fragments extracted: 734
  Total lines: 12,345
  Average quality: 6.8/10
  Languages: Python, JavaScript/TypeScript, Go
  Extraction time: 5.23s

Top 20 fragments by quality:
  1. UserAuthenticator (PythonClass) - Quality: 10/10, Lines: 45
  2. processPayment (JS/Function) - Quality: 9/10, Lines: 38
  ...
```

## Create a Collection

Export your best Python utilities:

```bash
autopsy-pro export \
  --fragments-file my_fragments.json \
  --name "python_utilities" \
  --description "High-quality Python utility functions" \
  --language python \
  --min-quality 7
```

## Common Workflows

### Workflow 1: Weekly Code Harvest

```bash
#!/bin/bash
# harvest.sh - Run weekly to collect code

DATE=$(date +%Y%m%d)

# Scan all projects
autopsy-pro scan ~/projects \
  --inactive-days 30 \
  --output "scans/scan_${DATE}.json"

# Extract quality fragments
autopsy-pro extract \
  --scan-file "scans/scan_${DATE}.json" \
  --min-quality 7 \
  --skip-tests \
  --output "fragments/fragments_${DATE}.json"

# Export by language
for lang in python javascript go; do
  autopsy-pro export \
    --fragments-file "fragments/fragments_${DATE}.json" \
    --name "${lang}_${DATE}" \
    --language "$lang" \
    --min-quality 7
done

echo "Harvest complete!"
```

### Workflow 2: Pre-Archive Cleanup

```bash
# Before archiving old projects, extract valuable code
autopsy-pro scan ~/projects-to-archive \
  --include-active \
  --output archive_scan.json

autopsy-pro extract \
  --scan-file archive_scan.json \
  --min-quality 5 \
  --output archive_code.json

# Review what you're keeping
autopsy-pro import archive_code.json --verbose
```

### Workflow 3: Learning Library

```bash
# Build a library of well-documented code examples
autopsy-pro extract ~/open-source-projects \
  --min-quality 8 \
  --output examples.json

autopsy-pro export \
  --fragments-file examples.json \
  --name "code_examples" \
  --description "Well-documented code examples for learning"
```

## Configuration Tips

### For Speed

```bash
# Optimize for fast scanning
autopsy-pro config --set parallel_scan=true
autopsy-pro config --set max_workers=8
autopsy-pro config --set enable_cache=true
```

### For Quality

```bash
# Extract only the best code
autopsy-pro config --set min_quality=7
autopsy-pro config --set min_lines=10
autopsy-pro config --set skip_tests=true
autopsy-pro config --set deduplicate=true
```

### For Coverage

```bash
# Don't miss anything
autopsy-pro config --set min_quality=3
autopsy-pro config --set inactive_days=7
autopsy-pro config --set include_active=true
```

## View Your Configuration

```bash
# See what settings you're using
autopsy-pro config --show
```

## Understanding Quality Scores

Fragments are scored 1-10:

- **9-10**: Excellent - Well-documented, typed, good structure
- **7-8**: Good - Clean code with some documentation
- **5-6**: Acceptable - Functional but could use improvement
- **3-4**: Poor - Minimal documentation, complex
- **1-2**: Very Poor - Debug code, TODOs, deep nesting

## Example Use Cases

### Extract API Utilities

```bash
# Find all high-quality API-related code
autopsy-pro extract ~/projects \
  --min-quality 6 \
  --output api_code.json

# Then filter the results
autopsy-pro export \
  --fragments-file api_code.json \
  --name "api_utilities" \
  --min-quality 7
```

### Migrate to New Framework

```bash
# Extract from legacy Django project
autopsy-pro scan ~/legacy-django \
  --include-active \
  --output legacy.json

autopsy-pro extract \
  --scan-file legacy.json \
  --min-quality 5 \
  --output django_code.json

# Review and select code to migrate
```

### Build Component Library

```bash
# Extract React components
autopsy-pro extract ~/react-projects \
  --min-quality 6 \
  --output components.json

autopsy-pro export \
  --fragments-file components.json \
  --language "javascript" \
  --name "react_components"
```

## Next Steps

1. **Explore your fragments**: Open the JSON files to see what was extracted
2. **Adjust quality thresholds**: Find the right balance for your needs
3. **Create collections**: Organize fragments by purpose or technology
4. **Automate**: Set up cron jobs or scripts for regular harvesting
5. **Build projects**: Use extracted code to bootstrap new projects (GUI coming soon)

## Troubleshooting Quick Reference

```bash
# Scan is slow
autopsy-pro config --set parallel_scan=true
autopsy-pro config --set max_workers=8

# Too many/few fragments
autopsy-pro config --set min_quality=7  # Increase for fewer, better quality
autopsy-pro config --set min_quality=4  # Decrease for more coverage

# Cache issues
autopsy-pro cache --clear

# Reset everything
autopsy-pro config --reset
autopsy-pro cache --clear
```

## Getting Help

```bash
# Command help
autopsy-pro --help
autopsy-pro scan --help
autopsy-pro extract --help

# View current settings
autopsy-pro config --show
```

---

Happy code harvesting! 🔍✨
