#!/usr/bin/env bash
# Sync the first Docker image version from compose.yaml.j2 to template.yaml
# This script is called by Renovate as a post-upgrade task

set -euo pipefail

# Find all template directories
find library/compose -type f -name "compose.yaml.j2" | while read -r compose_file; do
    template_dir=$(dirname "$compose_file")
    template_file="$template_dir/template.yaml"
    
    # Skip if template.yaml doesn't exist
    [ ! -f "$template_file" ] && continue
    
    # Extract the first image version from compose.yaml.j2
    # This matches: image: repo/name:version or image: name:version
    # Ignores Jinja2 variables like {{ variable }}
    version=$(grep -E '^\s*image:\s*[^{]*:[^{}\s]+' "$compose_file" | head -n1 | sed -E 's/.*:([^:]+)$/\1/' | tr -d ' ' || true)
    
    # Skip if no version found or if it's a Jinja2 variable
    if [ -z "$version" ] || [[ "$version" =~ \{\{ ]]; then
        continue
    fi
    
    # Get current template version and trim whitespace
    current_version=$(grep -E '^\s*version:\s*' "$template_file" | sed -E 's/.*version:\s*['\''"]?([^'\''"]+)['\''"]?/\1/' | tr -d ' ')
    
    # Only update if versions are different
    if [ -n "$current_version" ] && [ "$version" != "$current_version" ]; then
        echo "Updating $template_file: $current_version -> $version"
        
        # Use sed to update the version in template.yaml
        # Works on both macOS and Linux
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/version: .*/version: $version/" "$template_file"
        else
            sed -i "s/version: .*/version: $version/" "$template_file"
        fi
    fi
done

echo "Template version sync complete"
