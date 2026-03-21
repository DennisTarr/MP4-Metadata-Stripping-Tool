#!/bin/bash
# ============================================================
# MP4 Metadata Stripper Script - RECURSIVE VERSION
# Purpose: Remove all metadata from .mp4 files recursively
# Author: Qwen 3.5 35B-A3B (via AI Assistant)
# Last Updated: 2026-03-19
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
TARGET_DIR="."
DRY_RUN=false
BACKUP=false
VERBOSE=true
RECURSIVE=true       # Enable recursive by default

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)      DRY_RUN=true; shift ;;
        --backup)       BACKUP=true; shift ;;
        --no-verbose)   VERBOSE=false; shift ;;
        --non-recursive) RECURSIVE=false; shift ;;
        -h|--help)      
            echo "Usage: $0 [OPTIONS] [directory]"
            echo ""
            echo "Options:"
            echo "  --dry-run           Preview without changes"
            echo "  --backup            Create .bak backup files"
            echo "  --no-verbose        Suppress detailed output"
            echo "  --non-recursive     Only process current directory (default: recursive)"
            echo ""
            echo "Examples:"
            echo "  $0                          # Process all MP4 in current dir + subdirs"
            echo "  $0 ./videos                 # Process all MP4 in ./videos"
            echo "  $0 --backup .               # With backups"
            echo "  $0 --non-recursive .        # Current directory only"
            exit 0
            ;;
        *)              TARGET_DIR="$1"; shift ;;
    esac
done

# Validate directory
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${RED}ERROR: Directory '$TARGET_DIR' not found!${NC}"
    exit 1
fi

# Make path absolute
TARGET_DIR=$(cd "$TARGET_DIR" && pwd)

echo -e "${BLUE}=== MP4 Metadata Stripper (Recursive) ===${NC}"
echo "Directory: $TARGET_DIR"
echo "Dry run: $DRY_RUN | Backup: $BACKUP | Recursive: $RECURSIVE"
echo ""

# Collect all MP4 files using find with fallback to ls
FILES_OUTPUT=""

if [ "$RECURSIVE" = true ]; then
    # Try recursive find first
    FILES_OUTPUT=$(find "$TARGET_DIR" -type f \( -iname "*.mp4" \) 2>/dev/null || echo "")
    
    if [ -z "$FILES_OUTPUT" ] || [ "$(echo "$FILES_OUTPUT" | wc -l)" = "0" ]; then
        # Fallback: use ls with glob for current dir only
        FILES_OUTPUT=$(ls -1 "$TARGET_DIR"/*.mp4 2>/dev/null || echo "")
    fi
else
    # Non-recursive: just use ls glob
    FILES_OUTPUT=$(ls -1 "$TARGET_DIR"/*.mp4 2>/dev/null || echo "")
fi

# If still empty, try alternative approach with find and basename matching
if [ -z "$FILES_OUTPUT" ] || [ "$(echo "$FILES_OUTPUT" | wc -l)" = "0" ]; then
    if [ "$RECURSIVE" = true ]; then
        FILES_OUTPUT=$(find "$TARGET_DIR" -type f 2>/dev/null)
        # Filter for .mp4 files and apply pattern if needed
        FILTERED=""
        while IFS= read -r file; do
            bn=$(basename "$file")
            case "$bn" in
                *.mp4|*.MP4)
                    FILTERED="${FILTERED}${file}\n"
                    ;;
            esac
        done <<< "$FILES_OUTPUT"
        FILES_OUTPUT=$(echo -e "$FILTERED")
    fi
fi

# Count files
FILE_COUNT=0
if [ -n "$FILES_OUTPUT" ]; then
    FILE_COUNT=$(echo "$FILES_OUTPUT" | grep -c . 2>/dev/null || echo "0")
fi

if [ "$FILE_COUNT" = "0" ] || [ -z "$FILES_OUTPUT" ]; then
    echo -e "${YELLOW}No MP4 files found in: $TARGET_DIR${NC}"
    exit 0
fi

echo -e "${GREEN}Found ${FILE_COUNT} file(s) to process${NC}"
echo ""

# Process each file (using while read loop instead of array for compatibility)
processed=0
failed=0

while IFS= read -r file; do
    [ -z "$file" ] && continue
    
    basename_file=$(basename "$file")
    
    # Show relative path for clarity
    rel_path="${file#$TARGET_DIR/}"
    echo -e "${BLUE}Processing: $rel_path${NC}"
    
    # Create backup if requested
    if [ "$BACKUP" = true ]; then
        cp -p "$file" "${file}.bak" 2>/dev/null && \
            echo -e "  ${YELLOW}[BACKUP] Created .bak file${NC}" || \
            echo -e "  ${YELLOW}[SKIP] Backup failed or already exists${NC}"
    fi
    
    if [ "$DRY_RUN" = true ]; then
        meta_count=$(exiftool -s "$file" 2>/dev/null | wc -l)
        echo -e "  ${YELLOW}[DRY RUN] Would strip $meta_count metadata tags${NC}"
        processed=$((processed + 1))
        continue
    fi
    
    # Check file is readable
    if [ ! -r "$file" ]; then
        echo -e "  ${RED}✗ Cannot read file, skipping${NC}"
        failed=$((failed + 1))
        continue
    fi
    
    # Use exiftool to strip metadata in-place (safest method)
    echo -e "  ${YELLOW}[EXIFTOOL] Stripping all metadata...${NC}"
    
    if exiftool -all= "$file" 2>&1 | grep -q "updated"; then
        :
    fi
    
    # Actually strip the metadata
    result=$(exiftool -all= -overwrite_original "$file" 2>&1)
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Metadata stripped successfully${NC}"
        
        # Verify by checking remaining tags
        remaining=$(exiftool -s "$file" 2>/dev/null | wc -l)
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${BLUE}Metadata tags after stripping: $remaining${NC}"
        fi
        
        processed=$((processed + 1))
    else
        # Try alternative approach: copy to temp, strip, replace
        echo -e "  ${YELLOW}[EXIFTOOL] Trying copy method...${NC}"
        
        dir=$(dirname "$file")
        temp_file="${dir}/.${basename_file%.mp4}_clean.mp4"
        
        if exiftool -all= -o "$temp_file" "$file" >/dev/null 2>&1; then
            if [ -f "$temp_file" ] && [ -s "$temp_file" ]; then
                mv "$temp_file" "$file"
                echo -e "  ${GREEN}✓ Metadata stripped (copy method)${NC}"
                processed=$((processed + 1))
            else
                rm -f "$temp_file"
                echo -e "  ${RED}✗ Copy method failed, file empty or missing${NC}"
                failed=$((failed + 1))
            fi
        else
            echo -e "  ${RED}✗ Failed to strip metadata${NC}"
            echo -e "    Error: $result"
            failed=$((failed + 1))
        fi
    fi
    
    echo ""
done <<< "$FILES_OUTPUT"

# Summary
echo -e "${BLUE}=== SUMMARY ===${NC}"
echo -e "Processed successfully: ${GREEN}$processed${NC}"
if [ $failed -gt 0 ]; then
    echo -e "Failed: ${RED}$failed${NC}"
fi

exit 0
