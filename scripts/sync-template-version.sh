#!/usr/bin/env bash
# Sync Docker image versions to template.yaml metadata
# This script is triggered by GitHub Actions when Renovate updates dependencies
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

# Function to extract version from Docker image reference
# Handles: image:tag, registry/image:tag, registry/namespace/image:tag
extract_version_from_image() {
    local image_line="$1"
    # Extract everything after the last colon, excluding Jinja2 variables
    echo "$image_line" | sed -E 's/.*:([^:]+)$/\1/' | tr -d ' ' | grep -v '{{' || true
}

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

# Process Docker Compose templates
echo ""
echo "Scanning Docker Compose templates..."
while IFS= read -r compose_file; do
    template_dir=$(dirname "$compose_file")
    template_file="$template_dir/template.yaml"
    
    # Skip if template.yaml doesn't exist
    [ ! -f "$template_file" ] && continue
    
    # Extract the first Docker image version from compose.yaml.j2
    # Matches: image: repo/name:version or image: name:version
    # Ignores Jinja2 variables like {{ variable }}
    version=$(grep -E '^\s*image:\s*[^{]*:[^{}\s]+' "$compose_file" | head -n1 | sed -E 's/.*:([^:]+)$/\1/' | tr -d ' ' || true)
    
    # Skip if no version found or if it's a Jinja2 variable
    if [ -z "$version" ] || [[ "$version" =~ \{\{ ]]; then
        continue
    fi
    
    # Update template version
    if update_template_version "$template_file" "$version"; then
        ((updated_count++))
    fi
done < <(find library/compose -type f -name "compose.yaml.j2" 2>/dev/null || true)

# Process Kubernetes Helm templates (values.yaml pattern)
echo ""
echo "Scanning Kubernetes Helm templates..."
while IFS= read -r values_file; do
    template_dir=$(dirname "$values_file")
    template_file="$template_dir/template.yaml"
    
    # Skip if template.yaml doesn't exist
    [ ! -f "$template_file" ] && continue
    
    # Extract version from Helm values.yaml
    # Matches repository + tag pattern:
    #   repository: registry/image
    #   tag: version
    version=$(grep -A1 'repository:' "$values_file" | grep 'tag:' | sed -E 's/.*tag:\s*['\''"]?([^'\''" ]+)['\''"]?/\1/' | head -n1 | tr -d ' ' || true)
    
    # Skip if no version found or if it's a Jinja2 variable
    if [ -z "$version" ] || [[ "$version" =~ \{\{ ]]; then
        continue
    fi
    
    # Update template version
    if update_template_version "$template_file" "$version"; then
        ((updated_count++))
    fi
done < <(find library/kubernetes -type f \( -name "values.yaml" -o -name "values.yml" \) 2>/dev/null || true)

# Process Kubernetes manifest templates (*.j2 files with image: references)
echo ""
echo "Scanning Kubernetes manifest templates..."
while IFS= read -r manifest_file; do
    template_dir=$(dirname "$manifest_file")
    template_file="$template_dir/template.yaml"
    
    # Skip if template.yaml doesn't exist
    [ ! -f "$template_file" ] && continue
    
    # Extract the first Docker image version from Kubernetes manifest
    # Matches: image: repo/name:version or image: name:version
    # Ignores Jinja2 variables like {{ variable }}
    version=$(grep -E '^\s*image:\s*[^{]*:[^{}\s]+' "$manifest_file" | head -n1 | sed -E 's/.*:([^:]+)$/\1/' | tr -d ' ' || true)
    
    # Skip if no version found or if it's a Jinja2 variable
    if [ -z "$version" ] || [[ "$version" =~ \{\{ ]]; then
        continue
    fi
    
    # Update template version
    if update_template_version "$template_file" "$version"; then
        ((updated_count++))
    fi
done < <(find library/kubernetes -type f -name "*.j2" 2>/dev/null || true)

# Process Terraform/Packer templates if needed in the future
# (Currently no version syncing implemented for these)

echo ""
echo "=================================================="
if [ $updated_count -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Template version sync complete: ${GREEN}$updated_count${NC} template(s) updated"
else
    echo "No template version updates needed"
fi
echo "=================================================="
