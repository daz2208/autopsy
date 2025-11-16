#!/bin/bash
# Autopsy Pro v3 - Complete Workflow Demo
# This script demonstrates the full capability of Autopsy Pro v3

set -e  # Exit on error

echo "========================================="
echo "Autopsy Pro v3 - Complete Workflow Demo"
echo "========================================="
echo ""

# Change to the autopsy directory
cd "$(dirname "$0")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Scan for projects
echo -e "${BLUE}Step 1: Scanning for projects...${NC}"
python3 -m autopsy_pro_v3.cli scan autopsy_pro_v3 \
    --include-active \
    --output demo_scan.json \
    --verbose
echo -e "${GREEN}✓ Scan complete${NC}"
echo ""

# Step 2: Extract code fragments
echo -e "${BLUE}Step 2: Extracting code fragments (quality >= 7)...${NC}"
python3 -m autopsy_pro_v3.cli extract \
    --scan-file demo_scan.json \
    --min-quality 7 \
    --output demo_fragments.json \
    --verbose
echo -e "${GREEN}✓ Extraction complete${NC}"
echo ""

# Step 3: Export high-quality Python functions
echo -e "${BLUE}Step 3: Exporting high-quality Python functions...${NC}"
python3 -m autopsy_pro_v3.cli export \
    --fragments-file demo_fragments.json \
    --name "high_quality_python" \
    --min-quality 8
echo -e "${GREEN}✓ Export complete${NC}"
echo ""

# Step 4: View configuration
echo -e "${BLUE}Step 4: Current configuration...${NC}"
python3 -m autopsy_pro_v3.cli config --show
echo ""

# Step 5: Show cache status
echo -e "${BLUE}Step 5: Cache information...${NC}"
if [ -d "$HOME/.autopsy_pro/cache" ]; then
    cache_files=$(find "$HOME/.autopsy_pro/cache" -name "*.json" 2>/dev/null | wc -l)
    echo "Cache files: $cache_files"
else
    echo "No cache directory found"
fi
echo ""

# Summary
echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}Workflow Summary${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo "✓ Scanned projects and found code files"
echo "✓ Extracted quality code fragments"
echo "✓ Exported high-quality functions"
echo "✓ Configuration validated"
echo ""
echo "Output files created:"
echo "  - demo_scan.json (scan results)"
echo "  - demo_fragments.json (extracted fragments)"
echo "  - ~/.autopsy_pro/exports/high_quality_python.json (export)"
echo ""
echo -e "${GREEN}All steps completed successfully!${NC}"
