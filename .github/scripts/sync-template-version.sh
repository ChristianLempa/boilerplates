#!/usr/bin/env bash
# Sync Docker image versions to template.yaml metadata
# This script is triggered by GitHub Actions when Renovate updates dependencies
#
# Usage:
#   ./sync-template-version.sh                    # Process all templates
#   ./sync-template-version.sh file1 file2 ...    # Process specific files only
#
# Supports:
# - Docker Compose templates (compose.yaml.j2)
# - Kubernetes Helm templates (values.yaml, values.yml)
# - Kubernetes manifest templates (*.j2 files)

set -euo pipefail

# Color output for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Starting template version sync..."

# Function to update template.yaml version
update_template_version() {
    local template_file="$1"
    local new_version="$2"
    
    # Get current version from template.yaml
    local current_version
    current_version=$(grep -E '^\s*version:\s*' "$template_file" | sed -E 's/.*version:\s*['\''"]?([^'\''"]+)['\''"]?/\1/' | tr -d ' ' || true)
    
    # Only update if versions are different
    if [ -n "$current_version" ] && [ "$new_version" != "$current_version" ]; then
        echo -e "${GREEN}✓${NC} Updating $template_file: ${YELLOW}$current_version${NC} → ${GREEN}$new_version${NC}"
        
        # Update version in template.yaml (cross-platform compatible)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/version: .*/version: $new_version/" "$template_file"
        else
            sed -i "s/version: .*/version: $new_version/" "$template_file"
        fi
        return 0
    fi
    return 1
}

# Counter for updated templates
updated_count=0

# Determine which files to process
if [ $# -gt 0 ]; then
    # Process only specified files
    echo "Processing ${#@} changed file(s)..."
    FILES_TO_PROCESS=("$@")
else
    # Process all templates
    echo "Processing all templates..."
    mapfile -t FILES_TO_PROCESS < <(find library -type f \( -name "compose.yaml.j2" -o -name "values.yaml" -o -name "values.yml" \) 2>/dev/null || true)
fi

# Process each file
for file_path in "${FILES_TO_PROCESS[@]}"; do
    # Skip if file doesn't exist
    [ ! -f "$file_path" ] && continue
    
    template_dir=$(dirname "$file_path")
    template_file="$template_dir/template.yaml"
    
    # Skip if template.yaml doesn't exist
    [ ! -f "$template_file" ] && continue
    
    # Determine file type and extract version accordingly
    filename=$(basename "$file_path")
    version=""
    
    if [[ "$filename" == "compose.yaml.j2" ]]; then
        # Docker Compose template
        # Extract the first Docker image version
        # Matches: image: repo/name:version or image: name:version
        # Ignores Jinja2 variables like {{ variable }}
        version=$(grep -E '^\s*image:\s*[^{]*:[^{}\s]+' "$file_path" | head -n1 | sed -E 's/.*:([^:]+)$/\1/' | tr -d ' ' || true)
    elif [[ "$filename" == "values.yaml" ]] || [[ "$filename" == "values.yml" ]]; then
        # Kubernetes Helm values file
        # Extract version from repository + tag pattern
        version=$(grep -A1 'repository:' "$file_path" | grep 'tag:' | sed -E 's/.*tag:\s*['\''"]?([^'\''" ]+)['\''"]?/\1/' | head -n1 | tr -d ' ' || true)
    elif [[ "$filename" == *.j2 ]]; then
        # Kubernetes manifest template
        # Extract the first Docker image version
        version=$(grep -E '^\s*image:\s*[^{]*:[^{}\s]+' "$file_path" | head -n1 | sed -E 's/.*:([^:]+)$/\1/' | tr -d ' ' || true)
    fi
    
    # Skip if no version found or if it's a Jinja2 variable
    if [ -z "$version" ] || [[ "$version" =~ \{\{ ]]; then
        continue
    fi
    
    # Update template version
    if update_template_version "$template_file" "$version"; then
        ((updated_count++))
    fi
done

echo ""
echo "=================================================="
if [ $updated_count -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Template version sync complete: ${GREEN}$updated_count${NC} template(s) updated"
else
    echo "No template version updates needed"
fi
echo "=================================================="

# Exit successfully
exit 0
