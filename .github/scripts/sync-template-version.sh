#!/usr/bin/env bash
# Sync Docker image versions to template.yaml metadata
# Triggered by GitHub Actions when Renovate updates dependencies

set -euo pipefail

# Extract version from different file types
extract_version() {
    local file="$1"
    local filename=$(basename "$file")
    
    case "$filename" in
        compose.yaml.j2|*.j2)
            # Docker Compose or K8s manifest: extract from image: line
            grep -E '^\s*image:\s*[^{]*:[^{}\s]+' "$file" | head -n1 | sed -E 's/.*:([^:]+)$/\1/' | tr -d ' ' || true
            ;;
        values.yaml|values.yml)
            # Helm values: extract from repository + tag
            grep -A1 'repository:' "$file" | grep 'tag:' | sed -E 's/.*tag:\s*['\''"]?([^'\''"]+)['\''"]?/\1/' | tr -d ' ' || true
            ;;
    esac
}

# Update template.yaml if version differs
update_template() {
    local template_file="$1"
    local new_version="$2"
    local current_date=$(date +%Y-%m-%d)
    
    local current_version=$(grep -E '^\s*version:\s*' "$template_file" | sed -E 's/.*version:\s*['\''"]?([^'\''"]+)['\''"]?/\1/' | tr -d ' ' || true)
    
    if [ -n "$current_version" ] && [ "$new_version" != "$current_version" ]; then
        echo "✓ Updating $template_file: $current_version → $new_version (date: $current_date)"
        sed -i "s/version: .*/version: $new_version/" "$template_file"
        sed -i "s/date: .*/date: '$current_date'/" "$template_file"
        return 0
    fi
    return 1
}

# Main processing
updated=0
files=("${@:-$(find library -type f \( -name 'compose.yaml.j2' -o -name 'values.yaml' -o -name 'values.yml' \) 2>/dev/null)}")

for file in "${files[@]}"; do
    [ ! -f "$file" ] && continue
    
    template_file="$(dirname "$file")/template.yaml"
    [ ! -f "$template_file" ] && continue
    
    version=$(extract_version "$file")
    [ -z "$version" ] || [[ "$version" =~ \{\{ ]] && continue
    
    update_template "$template_file" "$version" && ((updated++)) || true
done

echo "Processed ${#files[@]} file(s), updated $updated template(s)"
exit 0
